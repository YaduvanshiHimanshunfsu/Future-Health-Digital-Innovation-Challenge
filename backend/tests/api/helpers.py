import re
from dataclasses import dataclass
from typing import Any

import httpx
from fastapi import FastAPI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import DEFAULT_PACKS_DIR
from app.country_packs.loader import CountryPack, load_pack
from app.models.case import CareCase
from app.privacy.audit import AuditTrail
from app.privacy.authz import Authz
from app.privacy.crypto import FieldCipher
from synthetic.generate import SyntheticPerson, build_bundle, load_personas
from tests.conftest import IdentityProvider

AD = "ae-abu-dhabi"
INDIA = "in-india"


def with_binary_columns_decoded(dump: str) -> str:
    """A database dump, plus the contents of its binary columns as text."""
    decoded = [
        bytes.fromhex(value).decode("utf-8", "replace")
        for value in re.findall(r"'\\x([0-9a-f]+)'", dump)
    ]
    return "\n".join([dump, *decoded])


def bundle_for(slug: str, *, pack: str = AD, report_id: str | None = None) -> dict[str, Any]:
    loaded = load_pack(DEFAULT_PACKS_DIR / pack)
    panel, people, _ = load_personas(pack)
    return build_bundle(people[slug], loaded, panel, report_id=report_id)


@dataclass
class Stack:
    """A running app on a real database, plus shortcuts for what most API tests do."""

    app: FastAPI
    http: httpx.AsyncClient
    idp: IdentityProvider
    factory: async_sessionmaker[AsyncSession]
    audit: AuditTrail
    cipher: FieldCipher
    pack: CountryPack
    panel: str
    people: dict[str, SyntheticPerson]

    def headers(self, **claims: Any) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.idp.token(**claims)}"}

    async def ingest(
        self,
        bundle: Any,
        *,
        pack: str = AD,
        roles: list[str] | None = None,
    ) -> httpx.Response:
        headers = self.headers(sub="lab-1", realm_access={"roles": roles or ["lab_service"]})
        headers["X-Country-Pack"] = pack
        return await self.http.post("/v1/reports:ingest", json=bundle, headers=headers)

    async def only_case(self) -> CareCase:
        async with self.factory() as session:
            cases = (await session.scalars(select(CareCase))).all()
        assert len(cases) == 1
        return cases[0]

    async def sign_in(self, sub: str, slug: str | None = None, *, pack: str = AD) -> dict[str, str]:
        """Provision a person and agree to the service terms, as the onboarding screens would."""
        claims: dict[str, Any] = {"sub": sub}
        if slug is not None:
            _, people, _ = load_personas(pack)
            claims["national_id"] = people[slug].national_id
        headers = self.headers(**claims)
        created = await self.http.post("/v1/me", json={"pack_code": pack}, headers=headers)
        assert created.status_code == 200, created.text
        agreed = await self.http.post(
            "/v1/me/service-consent",
            json={"terms_version": "1", "accepted": True},
            headers=headers,
        )
        assert agreed.status_code == 200, agreed.text
        return headers

    async def provision(
        self, sub: str, slug: str | None = None, *, pack: str = AD
    ) -> dict[str, str]:
        """Provision someone who hasn't agreed to the service terms yet."""
        claims: dict[str, Any] = {"sub": sub}
        if slug is not None:
            _, people, _ = load_personas(pack)
            claims["national_id"] = people[slug].national_id
        headers = self.headers(**claims)
        created = await self.http.post("/v1/me", json={"pack_code": pack}, headers=headers)
        assert created.status_code == 200, created.text
        return headers

    def staff(self, sub: str, role: str) -> dict[str, str]:
        return self.headers(sub=sub, realm_access={"roles": [role]})

    async def person_id(self, headers: dict[str, str]) -> str:
        response = await self.http.get("/v1/me", headers=headers)
        assert response.status_code == 200, response.text
        person_id: str = response.json()["id"]
        return person_id

    async def share(
        self,
        owner: dict[str, str],
        grantee: dict[str, str],
        kind: str = "share_full",
        days: int = 30,
    ) -> dict[str, Any]:
        code = await self.http.post("/v1/consents/receive-code", headers=grantee)
        assert code.status_code == 200, code.text
        granted = await self.http.post(
            "/v1/consents",
            json={
                "grantee_code": code.json()["code"],
                "kind": kind,
                "purpose": "family_support",
                "terms_version": "1",
                "duration_days": days,
            },
            headers=owner,
        )
        assert granted.status_code == 201, granted.text
        body: dict[str, Any] = granted.json()
        return body

    async def link_couple(
        self,
        first: dict[str, str],
        second: dict[str, str],
        *,
        relationship: str = "unrelated",
    ) -> str:
        created = await self.http.post(
            "/v1/couples", json={"relationship": relationship}, headers=first
        )
        assert created.status_code == 201, created.text
        joined = await self.http.post(
            "/v1/couples/join",
            json={"invite_code": created.json()["invite_code"], "relationship": relationship},
            headers=second,
        )
        assert joined.status_code == 200, joined.text
        couple_id: str = created.json()["id"]
        return couple_id

    async def agree_to_match(
        self, couple_id: str, headers: dict[str, str], reveal: str = "yes_no"
    ) -> None:
        response = await self.http.post(
            f"/v1/couples/{couple_id}/consent",
            json={
                "reveal_level": reveal,
                "terms_version": "1",
                "understood_what_a_result_reveals": True,
            },
            headers=headers,
        )
        assert response.status_code == 200, response.text

    async def ready_couple(
        self,
        first_slug: str,
        second_slug: str,
        *,
        reveals: tuple[str, str] = ("yes_no", "yes_no"),
        relationship: str = "unrelated",
    ) -> tuple[str, dict[str, str], dict[str, str]]:
        for slug in (first_slug, second_slug):
            assert (await self.ingest(bundle_for(slug))).status_code == 201
        first = await self.sign_in(f"{first_slug}-login", first_slug)
        second = await self.sign_in(f"{second_slug}-login", second_slug)
        couple_id = await self.link_couple(first, second, relationship=relationship)
        await self.agree_to_match(couple_id, first, reveals[0])
        await self.agree_to_match(couple_id, second, reveals[1])
        return couple_id, first, second

    def cut_off_authorisation(self) -> Authz:
        """Point the app at a port nothing listens on. Returns the real client, to put back."""
        real: Authz = self.app.state.authz
        self.app.state.authz = Authz("http://127.0.0.1:1", "none", timeout_seconds=0.2)
        return real
