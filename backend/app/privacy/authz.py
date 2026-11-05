import logging
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from http import HTTPStatus
from typing import Any

import httpx

from app.core.config import Settings

log = logging.getLogger("samvid.authz")

CONDITION = "not_expired"
_ALREADY_EXISTS = "already exists"
_DOES_NOT_EXIST = "does not exist"


class AuthzUnavailable(Exception):
    """OpenFGA couldn't be reached or gave no usable answer."""


class AuthzRejected(Exception):
    """OpenFGA understood the request and refused it, so retrying won't help."""


@dataclass(frozen=True, slots=True)
class RelationTuple:
    user: str
    relation: str
    object: str
    expires_at: datetime | None = None

    def key(self) -> dict[str, str]:
        return {"user": self.user, "relation": self.relation, "object": self.object}


def _timestamp(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


class Authz:
    """Relationship checks through OpenFGA.

    `check` answers False on any failure, so an outage means no access. Writes raise instead,
    because the caller has to know: a revocation that didn't happen must not look as if it did.
    """

    def __init__(
        self,
        api_url: str,
        store_name: str,
        *,
        token: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
        timeout_seconds: float = 2.0,
    ) -> None:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        self._client = httpx.AsyncClient(
            base_url=api_url.rstrip("/"),
            headers=headers,
            timeout=timeout_seconds,
            transport=transport,
        )
        self._store_name = store_name
        self._store_id: str | None = None
        self._model_id: str | None = None
        self.clock: Callable[[], datetime] = lambda: datetime.now(UTC)

    @classmethod
    def from_settings(cls, settings: Settings) -> "Authz":
        token = settings.openfga_token.get_secret_value() if settings.openfga_token else None
        return cls(settings.openfga_api_url, settings.openfga_store_name, token=token)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        try:
            return await self._client.request(method, path, **kwargs)
        except httpx.HTTPError as exc:
            raise AuthzUnavailable(type(exc).__name__) from exc

    async def _resolve(self) -> tuple[str, str]:
        """The store and its newest model. Bootstrapping creates both before the API starts."""
        if self._store_id and self._model_id:
            return self._store_id, self._model_id
        token: str | None = None
        store_id: str | None = None
        while store_id is None:
            params = {"continuation_token": token} if token else {}
            response = await self._request("GET", "/stores", params=params)
            if response.status_code != HTTPStatus.OK:
                raise AuthzUnavailable(f"stores: {response.status_code}")
            body = response.json()
            for store in body.get("stores", []):
                if store["name"] == self._store_name:
                    store_id = store["id"]
                    break
            token = body.get("continuation_token") or None
            if store_id is None and token is None:
                raise AuthzUnavailable("store not bootstrapped")
        response = await self._request(
            "GET", f"/stores/{store_id}/authorization-models", params={"page_size": 1}
        )
        models = response.json().get("authorization_models", [])
        if response.status_code != HTTPStatus.OK or not models:
            raise AuthzUnavailable("model not bootstrapped")
        self._store_id, self._model_id = store_id, models[0]["id"]
        return store_id, models[0]["id"]

    async def check(self, user: str, relation: str, obj: str) -> bool:
        try:
            store_id, model_id = await self._resolve()
            response = await self._request(
                "POST",
                f"/stores/{store_id}/check",
                json={
                    "tuple_key": {"user": user, "relation": relation, "object": obj},
                    "context": {"current_time": _timestamp(self.clock())},
                    "authorization_model_id": model_id,
                },
            )
            if response.status_code != HTTPStatus.OK:
                raise AuthzUnavailable(f"check: {response.status_code}")
            return response.json().get("allowed") is True
        except (AuthzUnavailable, ValueError, KeyError) as exc:
            log.warning("authz_check_failed", extra={"ctx": {"error": type(exc).__name__}})
            return False

    async def write(self, relation_tuple: RelationTuple) -> None:
        key: dict[str, Any] = relation_tuple.key()
        if relation_tuple.expires_at is not None:
            key["condition"] = {
                "name": CONDITION,
                "context": {"expires_at": _timestamp(relation_tuple.expires_at)},
            }
        await self._change({"writes": {"tuple_keys": [key]}}, tolerated=_ALREADY_EXISTS)

    async def delete(self, relation_tuple: RelationTuple) -> None:
        await self._change(
            {"deletes": {"tuple_keys": [relation_tuple.key()]}}, tolerated=_DOES_NOT_EXIST
        )

    async def _change(self, body: dict[str, Any], *, tolerated: str) -> None:
        """Writes can be repeated safely: the state someone asked for already being true is fine."""
        store_id, model_id = await self._resolve()
        response = await self._request(
            "POST",
            f"/stores/{store_id}/write",
            json={**body, "authorization_model_id": model_id},
        )
        if response.status_code == HTTPStatus.OK:
            return
        if response.status_code in (HTTPStatus.BAD_REQUEST, HTTPStatus.CONFLICT):
            if tolerated in response.text:
                return
            raise AuthzRejected(f"write: {response.status_code}")
        raise AuthzUnavailable(f"write: {response.status_code}")

    async def tuples(self) -> AsyncIterator[RelationTuple]:
        """Every stored tuple, for reconciling against the database."""
        store_id, _ = await self._resolve()
        token: str | None = None
        while True:
            body: dict[str, Any] = {"page_size": 100}
            if token:
                body["continuation_token"] = token
            response = await self._request("POST", f"/stores/{store_id}/read", json=body)
            if response.status_code != HTTPStatus.OK:
                raise AuthzUnavailable(f"read: {response.status_code}")
            page = response.json()
            for item in page.get("tuples", []):
                key = item["key"]
                yield RelationTuple(key["user"], key["relation"], key["object"])
            token = page.get("continuation_token") or None
            if token is None:
                return
