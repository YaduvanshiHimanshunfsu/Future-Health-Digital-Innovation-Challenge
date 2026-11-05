import base64
import os
from typing import Protocol

import httpx
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import Settings, decode_key

_WRAP_CONTEXT = b"samvid-dek-v1"


class KeyUnavailable(Exception):
    """The key service can't be reached or refused, so nothing can be encrypted or read."""


class KekProvider(Protocol):
    async def wrap(self, dek: bytes) -> bytes: ...

    async def unwrap(self, wrapped: bytes) -> bytes: ...


class LocalKek:
    """Development only. The settings refuse this provider in production."""

    def __init__(self, kek: bytes) -> None:
        if len(kek) != 32:
            raise ValueError("KEK must be 32 bytes")
        self._aead = AESGCM(kek)

    async def wrap(self, dek: bytes) -> bytes:
        nonce = os.urandom(12)
        return nonce + self._aead.encrypt(nonce, dek, _WRAP_CONTEXT)

    async def unwrap(self, wrapped: bytes) -> bytes:
        try:
            return self._aead.decrypt(wrapped[:12], wrapped[12:], _WRAP_CONTEXT)
        except InvalidTag as exc:
            raise KeyUnavailable("could not unwrap data key") from exc


class VaultTransitKek:
    """The master key stays inside Vault. It only ever sees and returns data keys."""

    def __init__(
        self,
        address: str,
        token: str,
        key_name: str,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base = f"{address.rstrip('/')}/v1/transit"
        self._headers = {"X-Vault-Token": token}
        self._key = key_name
        self._transport = transport

    async def _post(self, action: str, payload: dict[str, str]) -> dict[str, str]:
        url = f"{self._base}/{action}/{self._key}"
        try:
            async with httpx.AsyncClient(timeout=5.0, transport=self._transport) as client:
                response = await client.post(url, json=payload, headers=self._headers)
                response.raise_for_status()
            data: dict[str, str] = response.json()["data"]
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            raise KeyUnavailable(f"vault {action} failed") from exc
        return data

    async def wrap(self, dek: bytes) -> bytes:
        data = await self._post("encrypt", {"plaintext": base64.b64encode(dek).decode()})
        return data["ciphertext"].encode()

    async def unwrap(self, wrapped: bytes) -> bytes:
        data = await self._post("decrypt", {"ciphertext": wrapped.decode()})
        return base64.b64decode(data["plaintext"])


def build_kek(settings: Settings) -> KekProvider:
    if settings.kms_provider == "vault":
        if settings.vault_addr is None or settings.vault_token is None:
            raise ValueError("Vault needs VAULT_ADDR and VAULT_TOKEN")
        return VaultTransitKek(
            settings.vault_addr, settings.vault_token.get_secret_value(), settings.vault_transit_key
        )
    if settings.local_kek_b64 is None:
        raise ValueError("LOCAL_KEK_B64 is required")
    return LocalKek(decode_key(settings.local_kek_b64, "LOCAL_KEK_B64"))
