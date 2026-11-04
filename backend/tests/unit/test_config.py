import base64
import secrets
from typing import Any

import pytest
from pydantic import ValidationError

from tests.conftest import settings_for_tests


def production(**overrides: Any) -> dict[str, Any]:
    values: dict[str, Any] = {
        "env": "prod",
        "kms_provider": "vault",
        "local_kek_b64": None,
        "allowed_hosts": ["api.samvid.example"],
        "cors_origins": ["https://samvid.example"],
        "oidc_issuer": "https://idp.samvid.example/realms/samvid",
        "oidc_jwks_url": "https://idp.samvid.example/realms/samvid/protocol/openid-connect/certs",
    }
    values.update(overrides)
    return values


def test_valid_production_settings_load() -> None:
    assert settings_for_tests(**production()).is_production


def test_production_refuses_a_local_kek() -> None:
    with pytest.raises(ValidationError, match="local KEK"):
        settings_for_tests(**production(kms_provider="local", local_kek_b64=_key()))


@pytest.mark.parametrize("field", ["allowed_hosts", "cors_origins"])
def test_production_refuses_wildcards(field: str) -> None:
    with pytest.raises(ValidationError, match="wildcard"):
        settings_for_tests(**production(**{field: ["*"]}))


def test_production_refuses_plain_http_identity_provider() -> None:
    with pytest.raises(ValidationError, match="https"):
        settings_for_tests(**production(oidc_issuer="http://idp.samvid.example/realms/samvid"))
    with pytest.raises(ValidationError, match="https"):
        settings_for_tests(**production(oidc_jwks_url="http://idp.samvid.example/certs"))


def test_production_refuses_plain_http_cors_origin() -> None:
    with pytest.raises(ValidationError, match="https"):
        settings_for_tests(**production(cors_origins=["http://samvid.example"]))


def test_short_hmac_key_is_refused() -> None:
    with pytest.raises(ValidationError, match="at least 32 bytes"):
        settings_for_tests(audit_hmac_key=base64.b64encode(b"short").decode())


def test_non_base64_key_is_refused() -> None:
    with pytest.raises(ValidationError, match="base64"):
        settings_for_tests(audit_hmac_key="not base64!")


def test_one_key_cannot_serve_two_purposes() -> None:
    shared = _key()
    with pytest.raises(ValidationError, match="its own key"):
        settings_for_tests(audit_hmac_key=shared, national_id_hmac_key=shared)


def test_local_kms_needs_a_key() -> None:
    with pytest.raises(ValidationError, match="LOCAL_KEK_B64"):
        settings_for_tests(kms_provider="local", local_kek_b64=None)


def test_default_language_must_be_supported() -> None:
    with pytest.raises(ValidationError, match="default_language"):
        settings_for_tests(default_language="fr")


def test_comma_separated_lists_are_parsed() -> None:
    settings = settings_for_tests(allowed_hosts="a.example, b.example", supported_languages="en,hi")
    assert settings.allowed_hosts == ["a.example", "b.example"]
    assert settings.supported_languages == ["en", "hi"]


def test_secrets_do_not_appear_in_repr() -> None:
    key = _key()
    settings = settings_for_tests(audit_hmac_key=key)
    assert key not in repr(settings)
    assert key not in str(settings.model_dump())


def _key() -> str:
    return base64.b64encode(secrets.token_bytes(32)).decode()
