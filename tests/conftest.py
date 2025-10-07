import os
from pathlib import Path

import httpx
import pytest

from most.api import MostClient


DEFAULT_STAGE_CONFIG = {
    "MOST_CLIENT_ID": "68e4e7eb8c18d2d12f5e5b3e",
    "MOST_CLIENT_SECRET": "whiDsDZmrFWqVWqt1RqDcA$1IWg6yav50qWiGbm3f424JZ8niw03rdf4WokNIYOgB8",
    "MOST_BASE_URL": "https://api-stage.mostcontrol.ru/api/external",
}


@pytest.fixture()
def most_client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> MostClient:
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
        pytest.skip(f"MOST API unavailable: {exc}")

    if not model_id:
        try:
            models = client.list_models()
        except httpx.HTTPError as exc:
            pytest.skip(f"Unable to list MOST models: {exc}")
        if not models:
            pytest.skip("MOST API returned no models for the configured client")
        client.model_id = models[0].model_id
    try:
        yield client
    finally:
        client.session.close()
