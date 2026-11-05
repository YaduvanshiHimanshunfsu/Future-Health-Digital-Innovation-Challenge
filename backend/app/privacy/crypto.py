import json
import os
import struct
from typing import Any

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.privacy.kms import KekProvider

_FORMAT_VERSION = 1
_HEADER = struct.Struct(">BH")  # format version, length of the wrapped data key
_NONCE_BYTES = 12


class DecryptionError(Exception):
    """The record is corrupt, was tampered with, or belongs to a different row."""


class FieldCipher:
    """Envelope encryption: each record gets its own data key, wrapped by the master key.

    The caller names the row as associated data, like "carrier_finding:<id>". A ciphertext copied
    onto another row then fails to decrypt, instead of quietly showing one person another's result.
    """

    def __init__(self, kek: KekProvider) -> None:
        self._kek = kek

    async def encrypt_json(self, value: Any, *, aad: str) -> bytes:
        data_key = AESGCM.generate_key(bit_length=256)
        nonce = os.urandom(_NONCE_BYTES)
        plaintext = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        ciphertext = AESGCM(data_key).encrypt(nonce, plaintext, aad.encode())
        wrapped = await self._kek.wrap(data_key)
        return _HEADER.pack(_FORMAT_VERSION, len(wrapped)) + wrapped + nonce + ciphertext

    async def decrypt_json(self, blob: bytes, *, aad: str) -> Any:
        try:
            version, wrapped_length = _HEADER.unpack_from(blob)
        except struct.error as exc:
            raise DecryptionError("truncated record") from exc
        if version != _FORMAT_VERSION:
            raise DecryptionError("unknown record format")

        start = _HEADER.size
        wrapped = blob[start : start + wrapped_length]
        nonce = blob[start + wrapped_length : start + wrapped_length + _NONCE_BYTES]
        ciphertext = blob[start + wrapped_length + _NONCE_BYTES :]
        if len(wrapped) != wrapped_length or len(nonce) != _NONCE_BYTES or not ciphertext:
            raise DecryptionError("truncated record")

        data_key = await self._kek.unwrap(wrapped)
        try:
            return json.loads(AESGCM(data_key).decrypt(nonce, ciphertext, aad.encode()))
        except (InvalidTag, ValueError) as exc:
            raise DecryptionError("record failed authentication") from exc
