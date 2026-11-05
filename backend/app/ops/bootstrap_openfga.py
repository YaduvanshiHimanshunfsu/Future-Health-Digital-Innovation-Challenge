"""Creates the OpenFGA store and loads the model. Safe to run on every start."""

import asyncio
import json
import sys
from http import HTTPStatus
from pathlib import Path
from typing import Any

import httpx

from app.core.config import get_settings

MODEL_FILE = Path(__file__).resolve().parents[1] / "privacy" / "authz_model.json"
_ADDED_BY_OPENFGA = frozenset({"module", "source_info"})


def load_model() -> dict[str, Any]:
    model: dict[str, Any] = json.loads(MODEL_FILE.read_text("utf-8"))
    return model


async def _find_store(client: httpx.AsyncClient, name: str) -> str | None:
    token: str | None = None
    while True:
        response = await client.get(
            "/stores", params={"continuation_token": token} if token else {}
        )
        response.raise_for_status()
        body = response.json()
        for store in body.get("stores", []):
            if store["name"] == name:
                found: str = store["id"]
                return found
        token = body.get("continuation_token") or None
        if token is None:
            return None


def _meaning(value: Any) -> Any:
    """A model without what OpenFGA adds when it stores one: empty fields and source locations."""
    if isinstance(value, list):
        return [_meaning(item) for item in value]
    if not isinstance(value, dict):
        return value
    cleaned = {key: _meaning(item) for key, item in value.items() if key not in _ADDED_BY_OPENFGA}
    # {"this": {}} is the one empty value that means something.
    return {
        key: item
        for key, item in cleaned.items()
        if key == "this" or item not in (None, "", [], {})
    }


def _same_model(stored: dict[str, Any], wanted: dict[str, Any]) -> bool:
    return all(
        _meaning(stored.get(key)) == _meaning(wanted[key])
        for key in ("type_definitions", "conditions")
    )


async def bootstrap(
    api_url: str,
    store_name: str,
    *,
    token: str | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
) -> tuple[str, str]:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    async with httpx.AsyncClient(
        base_url=api_url.rstrip("/"), headers=headers, timeout=10.0, transport=transport
    ) as client:
        store_id = await _find_store(client, store_name)
        if store_id is None:
            created = await client.post("/stores", json={"name": store_name})
            created.raise_for_status()
            store_id = created.json()["id"]

        wanted = load_model()
        latest = await client.get(
            f"/stores/{store_id}/authorization-models", params={"page_size": 1}
        )
        latest.raise_for_status()
        models = latest.json().get("authorization_models", [])
        if models and _same_model(models[0], wanted):
            return str(store_id), str(models[0]["id"])

        written = await client.post(f"/stores/{store_id}/authorization-models", json=wanted)
        if written.status_code != HTTPStatus.CREATED:
            raise RuntimeError(f"OpenFGA refused the model: {written.status_code}")
        return str(store_id), str(written.json()["authorization_model_id"])


def main() -> int:
    settings = get_settings()
    token = settings.openfga_token.get_secret_value() if settings.openfga_token else None
    store_id, model_id = asyncio.run(
        bootstrap(settings.openfga_api_url, settings.openfga_store_name, token=token)
    )
    sys.stdout.write(f"OpenFGA ready: store {store_id}, model {model_id}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
