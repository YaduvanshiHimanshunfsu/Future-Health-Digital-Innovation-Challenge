import base64
import json
import os
import uuid

import httpx
import pytest

from app.privacy.crypto import DecryptionError, FieldCipher
from app.privacy.kms import KeyUnavailable, LocalKek, VaultTransitKek, build_kek
from tests.conftest import settings_for_tests

SECRET = {"gene": "HBB", "variant": "c.20A>T", "classification": "P"}


@pytest.fixture
def cipher() -> FieldCipher:
    return FieldCipher(LocalKek(os.urandom(32)))


async def test_round_trip(cipher: FieldCipher) -> None:
    blob = await cipher.encrypt_json(SECRET, aad="carrier_finding:1")
    assert await cipher.decrypt_json(blob, aad="carrier_finding:1") == SECRET


async def test_unicode_round_trip(cipher: FieldCipher) -> None:
    value = {"note": "परिवार"}
    assert await cipher.decrypt_json(await cipher.encrypt_json(value, aad="r"), aad="r") == value


async def test_ciphertext_holds_no_plaintext(cipher: FieldCipher) -> None:
    blob = await cipher.encrypt_json(SECRET, aad="r")
    for fragment in (b"HBB", b"c.20A", b"gene", b"classification"):
        assert fragment not in blob


async def test_same_value_encrypts_differently_each_time(cipher: FieldCipher) -> None:
    first = await cipher.encrypt_json(SECRET, aad="r")
    second = await cipher.encrypt_json(SECRET, aad="r")
    assert first != second


async def test_ciphertext_copied_to_another_row_fails(cipher: FieldCipher) -> None:
    """V2.1.2. Swapping two people's encrypted findings must not quietly show the wrong result."""
    row_a, row_b = uuid.uuid4(), uuid.uuid4()
    blob = await cipher.encrypt_json(SECRET, aad=f"carrier_finding:{row_a}")
    with pytest.raises(DecryptionError):
        await cipher.decrypt_json(blob, aad=f"carrier_finding:{row_b}")


@pytest.mark.parametrize("offset", [3, 40, -1], ids=["wrapped_key", "body", "auth_tag"])
async def test_flipping_any_byte_is_detected(cipher: FieldCipher, offset: int) -> None:
    """V2.1.3."""
    blob = bytearray(await cipher.encrypt_json(SECRET, aad="r"))
    blob[offset] ^= 0x01
    with pytest.raises((DecryptionError, KeyUnavailable)):
        await cipher.decrypt_json(bytes(blob), aad="r")


@pytest.mark.parametrize("length", [0, 2, 10, 40, 70])
async def test_truncated_records_are_refused(cipher: FieldCipher, length: int) -> None:
    blob = await cipher.encrypt_json(SECRET, aad="r")
    with pytest.raises((DecryptionError, KeyUnavailable)):
        await cipher.decrypt_json(blob[:length], aad="r")


async def test_unknown_format_version_is_refused(cipher: FieldCipher) -> None:
    blob = bytearray(await cipher.encrypt_json(SECRET, aad="r"))
    blob[0] = 99
    with pytest.raises(DecryptionError, match="format"):
        await cipher.decrypt_json(bytes(blob), aad="r")


async def test_another_master_key_cannot_read_it(cipher: FieldCipher) -> None:
    blob = await cipher.encrypt_json(SECRET, aad="r")
    other = FieldCipher(LocalKek(os.urandom(32)))
    with pytest.raises(KeyUnavailable):
        await other.decrypt_json(blob, aad="r")


def test_short_master_key_is_refused() -> None:
    with pytest.raises(ValueError, match="32 bytes"):
        LocalKek(b"short")


class FakeVault:
    def __init__(self) -> None:
        self.available = True
        self.seen_tokens: list[str] = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.seen_tokens.append(request.headers.get("X-Vault-Token", ""))
        if not self.available:
            return httpx.Response(503)
        body = json.loads(request.content)
        if request.url.path.endswith("/encrypt/samvid-kek"):
            return httpx.Response(
                200, json={"data": {"ciphertext": "vault:v1:" + body["plaintext"]}}
            )
        if request.url.path.endswith("/decrypt/samvid-kek"):
            return httpx.Response(
                200, json={"data": {"plaintext": body["ciphertext"].removeprefix("vault:v1:")}}
            )
        return httpx.Response(404)


async def test_vault_wraps_and_unwraps_through_its_api() -> None:
    vault = FakeVault()
    kek = VaultTransitKek(
        "https://vault.test", "t0ken", "samvid-kek", transport=httpx.MockTransport(vault.handler)
    )
    cipher = FieldCipher(kek)
    blob = await cipher.encrypt_json(SECRET, aad="r")
    assert await cipher.decrypt_json(blob, aad="r") == SECRET
    assert set(vault.seen_tokens) == {"t0ken"}
    assert b"vault:v1:" in blob


async def test_vault_outage_fails_closed() -> None:
    vault = FakeVault()
    kek = VaultTransitKek(
        "https://vault.test", "t", "samvid-kek", transport=httpx.MockTransport(vault.handler)
    )
    cipher = FieldCipher(kek)
    blob = await cipher.encrypt_json(SECRET, aad="r")
    vault.available = False
    with pytest.raises(KeyUnavailable):
        await cipher.decrypt_json(blob, aad="r")
    with pytest.raises(KeyUnavailable):
        await cipher.encrypt_json(SECRET, aad="r")


def test_build_kek_uses_the_configured_provider() -> None:
    assert isinstance(build_kek(settings_for_tests()), LocalKek)
    vault = build_kek(
        settings_for_tests(
            kms_provider="vault", local_kek_b64=None, vault_addr="https://v.test", vault_token="t"
        )
    )
    assert isinstance(vault, VaultTransitKek)


def test_vault_without_an_address_is_refused() -> None:
    with pytest.raises(ValueError, match="VAULT_ADDR"):
        build_kek(settings_for_tests(kms_provider="vault", local_kek_b64=None))


def test_base64_key_is_really_32_bytes() -> None:
    settings = settings_for_tests()
    assert settings.local_kek_b64 is not None
    assert len(base64.b64decode(settings.local_kek_b64.get_secret_value())) == 32
