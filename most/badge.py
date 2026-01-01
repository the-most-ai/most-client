import os
from datetime import datetime
from typing import Union, Optional

import httpx

from ._constrants import DEFAULT_MAX_RETRIES, DEFAULT_TIMEOUT
from .types import Audio
from .utils import generate_ed25519_keypair, sign_ed25519


class Badge(object):

    def __init__(self,
                 sn: str,
                 private_key: str,
                 badge_id: Optional[str] = None,

                 admin_api_key: Optional[str] = None,

                 base_url: str | httpx.URL | None = None,
                 timeout: Union[float, httpx.Timeout] = DEFAULT_TIMEOUT,
                 max_retries: int = DEFAULT_MAX_RETRIES,
                 # retry_delay: float = DEFAULT_RETRY_DELAY,
                 http_client: httpx.Client | None = None):
        self.sn = sn
        self.private_key = private_key

        if base_url is None:
            base_url = os.environ.get("MOST_BASE_URL")
        if base_url is None:
            base_url = f"https://api.the-most.ai/api/external"

        if http_client is None:
            http_client = httpx.Client(base_url=base_url,
                                       timeout=timeout,
                                       follow_redirects=True,
                                       transport=httpx.HTTPTransport(retries=max_retries))
        # self.max_retries = max_retries
        # self.retry_delay = retry_delay
        self.session = http_client
        self.admin_api_key = admin_api_key

        self.badge_id = badge_id
        self.token = None

    @classmethod
    def create(cls):
        sn, private_key = generate_ed25519_keypair()
        return cls(sn, private_key)

    def obtain_badge_id(self):
        r = self.session.get(f"/badge/check",
                             params={"sn": self.sn})
        r.raise_for_status()
        r = r.json()
        status = r["status"]
        if status == "ok":
            self.badge_id = r["id"]
            return self.badge_id
        return None

    def is_registered(self):
        return self.obtain_badge_id() is not None

    def register(self):
        r = self.session.post(
            "/badge/register",
            json={"sn": self.sn},
            headers={"Authorization": f"Basic {self.admin_api_key}"}
        )

        r.raise_for_status()
        self.badge_id = r.json()["id"]
        return self.badge_id

    def login(self):
        if self.badge_id is None:
            badge_id = self.obtain_badge_id()
            if badge_id is None:
                raise RuntimeError("Failed to obtain badge id: first register badge!")
        else:
            badge_id = self.badge_id

        r = self.session.get(
            "/badge/gen_token",
            params={"badge_id": badge_id},
        )

        r.raise_for_status()
        challenge = r.json()["challenge"]

        signature = sign_ed25519(self.private_key, challenge)

        r = self.session.post(
            "/badge/auth",
            json={
                "badge_id": badge_id,
                "signature_b64": signature,
            },
        )

        r.raise_for_status()
        self.token = r.json()["token"]

    def upload_audio(self, audio_path,
                     start_dt: datetime,
                     end_dt: datetime) -> Audio:
        start = int(start_dt.timestamp())
        end = int(end_dt.timestamp())
        with open(audio_path, 'rb') as f:
            resp = self.session.post(f"/badge/audio/upload",
                                     params={
                                         "start": start,
                                         "end": end,
                                     },
                                     files={"audio_file": f},
                                     headers={"X-Badge-Token": f"Bearer {self.token}"})
            resp.raise_for_status()
            return Audio(**resp.json())
