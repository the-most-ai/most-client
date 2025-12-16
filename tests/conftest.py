import os
from pathlib import Path

import httpx
import pytest

from most.api import MostClient


DEFAULT_STAGE_CONFIG = {
    "MOST_CLIENT_ID": "67239029570a08554fc1f5a6",
    "MOST_CLIENT_SECRET": "iXGO0XpvjRFC6H1vrXVOqQ$U0bGDpEUt09pOeIzVmS0G1v1dOrjNeC.1V3iDlKhfZc",
    "MOST_BASE_URL": "https://api.the-most.ai/api/external",
}


@pytest.fixture()
def most_client_e2e(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> MostClient:
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))

    client_id = os.environ.get("MOST_CLIENT_ID") or DEFAULT_STAGE_CONFIG["MOST_CLIENT_ID"]
    client_secret = (
        os.environ.get("MOST_CLIENT_SECRET") or DEFAULT_STAGE_CONFIG["MOST_CLIENT_SECRET"]
    )
    base_url = os.environ.get("MOST_BASE_URL") or DEFAULT_STAGE_CONFIG["MOST_BASE_URL"]
    model_id = os.environ.get("MOST_MODEL_ID")

    try:
        client = MostClient(
            client_id=client_id,
            client_secret=client_secret,
            base_url=base_url,
            model_id=model_id,
        )
    except httpx.HTTPError as exc:
        pytest.fail(f"MOST API unavailable: {exc}")

    if not model_id:
        try:
            models = client.list_models()
        except httpx.HTTPError as exc:
            pytest.fail(f"Unable to list MOST models: {exc}")
        if models:
            client = models[0]
    try:
        yield client
    finally:
        client.session.close()
