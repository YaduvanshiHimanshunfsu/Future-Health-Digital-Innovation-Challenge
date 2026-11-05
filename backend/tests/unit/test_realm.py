import json
from pathlib import Path
from typing import Any

import pytest

REALM_FILE = Path(__file__).resolve().parents[3] / "infra" / "keycloak" / "realm-samvid.json"


@pytest.fixture(scope="module")
def realm() -> dict[str, Any]:
    loaded: dict[str, Any] = json.loads(REALM_FILE.read_text("utf-8"))
    return loaded


@pytest.fixture(scope="module")
def user_profile(realm: dict[str, Any]) -> dict[str, Any]:
    provider = realm["components"]["org.keycloak.userprofile.UserProfileProvider"][0]
    loaded: dict[str, Any] = json.loads(provider["config"]["kc.user.profile.config"][0])
    return loaded


def test_people_cannot_see_or_edit_their_national_id(user_profile: dict[str, Any]) -> None:
    """Only a token decides whose results someone gets, so a person must never be able to set it."""
    field = next(a for a in user_profile["attributes"] if a["name"] == "national_id")
    assert field["permissions"] == {"view": ["admin"], "edit": ["admin"]}


def test_undeclared_attributes_stay_switched_off(user_profile: dict[str, Any]) -> None:
    assert user_profile.get("unmanagedAttributePolicy") in (None, "DISABLED")


def test_only_the_web_client_receives_the_national_id(realm: dict[str, Any]) -> None:
    holders = [
        client["clientId"]
        for client in realm["clients"]
        for mapper in client.get("protocolMappers", [])
        if mapper["config"].get("claim.name") == "national_id"
    ]
    assert holders == ["samvid-web"]


def test_the_claim_stays_out_of_id_tokens_and_userinfo(realm: dict[str, Any]) -> None:
    web = next(c for c in realm["clients"] if c["clientId"] == "samvid-web")
    mapper = next(m for m in web["protocolMappers"] if m["name"] == "national-id")
    assert mapper["config"]["id.token.claim"] == "false"
    assert mapper["config"]["userinfo.token.claim"] == "false"


def test_people_cannot_register_themselves_or_use_password_grants(realm: dict[str, Any]) -> None:
    assert realm["registrationAllowed"] is False
    assert all(client.get("directAccessGrantsEnabled") is not True for client in realm["clients"])
