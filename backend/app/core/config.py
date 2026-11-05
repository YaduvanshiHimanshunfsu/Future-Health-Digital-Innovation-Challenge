import base64
import binascii
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal
from urllib.parse import urlsplit

from pydantic import AnyHttpUrl, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

MIN_KEY_BYTES = 32
DEFAULT_PACKS_DIR = Path(__file__).resolve().parents[2] / "packs"

CommaList = Annotated[list[str], NoDecode]


def decode_key(value: SecretStr, name: str) -> bytes:
    try:
        raw = base64.b64decode(value.get_secret_value(), validate=True)
    except binascii.Error as exc:
        raise ValueError(f"{name} must be base64") from exc
    if len(raw) < MIN_KEY_BYTES:
        raise ValueError(f"{name} must decode to at least {MIN_KEY_BYTES} bytes")
    return raw


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    env: Literal["dev", "test", "prod"] = "dev"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    database_url: SecretStr
    redis_url: SecretStr

    allowed_hosts: CommaList = ["localhost", "127.0.0.1"]
    cors_origins: CommaList = []
    max_body_bytes: int = Field(default=1_000_000, gt=0, le=10_000_000)

    supported_languages: CommaList = ["en", "ar", "hi"]
    default_language: str = "en"

    oidc_issuer: AnyHttpUrl
    oidc_audience: str = "samvid-api"
    oidc_jwks_url: AnyHttpUrl
    jwks_ttl_seconds: int = Field(default=300, ge=30)
    jwks_refresh_cooldown_seconds: int = Field(default=30, ge=1)
    jwt_leeway_seconds: int = Field(default=30, ge=0, le=120)

    openfga_api_url: str = "http://127.0.0.1:8081"
    openfga_store_name: str = "samvid"
    openfga_token: SecretStr | None = None

    kms_provider: Literal["local", "vault"] = "local"
    local_kek_b64: SecretStr | None = None
    vault_addr: str | None = None
    vault_token: SecretStr | None = None
    vault_transit_key: str = "samvid-kek"

    audit_hmac_key: SecretStr
    invite_hmac_key: SecretStr
    national_id_hmac_key: SecretStr
    analytics_hmac_key: SecretStr

    llm_provider: Literal["template", "azure", "openai_compat"] = "template"

    packs_dir: Path = DEFAULT_PACKS_DIR
    enabled_packs: CommaList = ["ae-abu-dhabi", "in-india"]
    default_pack: str = "ae-abu-dhabi"

    # How far to trust an authenticated lab client's reports. "demo" treats them as attested for the
    # prototype, since real signature checks need a real lab. Refused in production.
    lab_attestation: Literal["demo", "unverified", "verified"] = "demo"

    @field_validator(
        "allowed_hosts", "cors_origins", "supported_languages", "enabled_packs", mode="before"
    )
    @classmethod
    def _split_commas(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator(
        "audit_hmac_key", "invite_hmac_key", "national_id_hmac_key", "analytics_hmac_key"
    )
    @classmethod
    def _key_is_strong(cls, value: SecretStr) -> SecretStr:
        decode_key(value, "HMAC key")
        return value

    @model_validator(mode="after")
    def _consistent(self) -> "Settings":
        if self.default_language not in self.supported_languages:
            raise ValueError("default_language must be one of supported_languages")
        hmac_keys = [
            self.audit_hmac_key,
            self.invite_hmac_key,
            self.national_id_hmac_key,
            self.analytics_hmac_key,
        ]
        if len({key.get_secret_value() for key in hmac_keys}) != len(hmac_keys):
            # Reusing one key would let an audit HMAC double as an identity blind index.
            raise ValueError("each HMAC purpose needs its own key")
        if self.kms_provider == "local":
            if self.local_kek_b64 is None:
                raise ValueError("LOCAL_KEK_B64 is required when KMS_PROVIDER=local")
            decode_key(self.local_kek_b64, "LOCAL_KEK_B64")
        if self.default_pack not in self.enabled_packs:
            raise ValueError("default_pack must be one of enabled_packs")
        if self.env == "prod":
            self._check_production()
        return self

    def _check_production(self) -> None:
        if self.kms_provider == "local":
            raise ValueError("a local KEK is not allowed in production")
        if not self.openfga_api_url.startswith("https://") or not self.openfga_token:
            raise ValueError("production needs OPENFGA_API_URL over https and OPENFGA_TOKEN")
        if self.lab_attestation == "demo":
            raise ValueError("demo lab attestation is not allowed in production")
        if (
            not self.vault_addr
            or not self.vault_addr.startswith("https://")
            or not self.vault_token
        ):
            raise ValueError("production needs VAULT_ADDR over https and VAULT_TOKEN")
        if "*" in self.allowed_hosts or "*" in self.cors_origins:
            raise ValueError("wildcard hosts or origins are not allowed in production")
        for name, url in (("OIDC_ISSUER", self.oidc_issuer), ("OIDC_JWKS_URL", self.oidc_jwks_url)):
            if url.scheme != "https":
                raise ValueError(f"{name} must use https in production")
        for origin in self.cors_origins:
            if urlsplit(origin).scheme != "https":
                raise ValueError("CORS origins must use https in production")

    @property
    def is_production(self) -> bool:
        return self.env == "prod"

    @property
    def issuer(self) -> str:
        return str(self.oidc_issuer).rstrip("/")


@lru_cache
def get_settings() -> Settings:
    return Settings()
