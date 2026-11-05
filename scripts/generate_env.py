"""Create infra/.env with fresh random secrets for local development.

Never changes a value already there, because that would lock you out of the current database. If
the file exists, only settings added since it was created get filled in.
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
    values = {
        "POSTGRES_SUPERUSER_PASSWORD": password(),
        "SAMVID_OWNER_PASSWORD": password(),
        "SAMVID_APP_PASSWORD": password(),
        "OPENFGA_DB_PASSWORD": password(),
        "OPENFGA_PRESHARED_KEY": password(),
        "REDIS_PASSWORD": password(),
        "KEYCLOAK_ADMIN_PASSWORD": password(),
        "LAB_CLIENT_SECRET": password(),
        "LOCAL_KEK_B64": key(),
        "AUDIT_HMAC_KEY": key(),
        "INVITE_HMAC_KEY": key(),
        "NATIONAL_ID_HMAC_KEY": key(),
        "ANALYTICS_HMAC_KEY": key(),
        "WEB_SESSION_SECRET": key(),
        "DEMO_PASSWORD": password(),
    }
    existing = TARGET.read_text(encoding="utf-8") if TARGET.exists() else ""
    present = {line.split("=", 1)[0] for line in existing.splitlines() if "=" in line}
    missing = {name: value for name, value in values.items() if name not in present}
    if not missing:
        sys.stdout.write(f"{TARGET} is already complete.\n")
        return 0
    separator = "" if not existing or existing.endswith("\n") else "\n"
    addition = "\n".join(f"{name}={value}" for name, value in missing.items()) + "\n"
    TARGET.write_text(existing + separator + addition, encoding="utf-8")
    sys.stdout.write(f"Wrote {len(missing)} new settings to {TARGET}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
