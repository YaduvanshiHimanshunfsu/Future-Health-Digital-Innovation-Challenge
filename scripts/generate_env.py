"""Create infra/.env with fresh random secrets for local development.

Refuses to overwrite an existing file, because that would lock you out of the current database.
"""

import base64
import secrets
import sys
from pathlib import Path

TARGET = Path(__file__).resolve().parent.parent / "infra" / ".env"


def password() -> str:
    # URL-safe, since these end up inside connection strings.
    return secrets.token_urlsafe(24)


def key() -> str:
    return base64.b64encode(secrets.token_bytes(32)).decode()


def main() -> int:
    if TARGET.exists():
        print(f"{TARGET} already exists. Delete it first if you really want new secrets.")
        return 1
    values = {
        "POSTGRES_SUPERUSER_PASSWORD": password(),
        "SAMVID_OWNER_PASSWORD": password(),
        "SAMVID_APP_PASSWORD": password(),
        "OPENFGA_DB_PASSWORD": password(),
        "REDIS_PASSWORD": password(),
        "KEYCLOAK_ADMIN_PASSWORD": password(),
        "LAB_CLIENT_SECRET": password(),
        "LOCAL_KEK_B64": key(),
        "AUDIT_HMAC_KEY": key(),
        "INVITE_HMAC_KEY": key(),
        "NATIONAL_ID_HMAC_KEY": key(),
        "ANALYTICS_HMAC_KEY": key(),
    }
    TARGET.write_text(
        "\n".join(f"{name}={value}" for name, value in values.items()) + "\n", encoding="utf-8"
    )
    print(f"Wrote {TARGET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
