from typing import List
import json5
from adaptix import Retort
from most.types import Audio, Result, Script, JobStatus, Text
from pathlib import Path
import httpx


class AsyncMostClient(object):
    retort = Retort()

    def __init__(self,
                 client_id=None,
                 client_secret=None,
                 model_id=None):
        super(AsyncMostClient, self).__init__()
        self.client_id = client_id
        self.client_secret = client_secret

        if self.client_id is None:
            credentials = self.load_credentials()
            self.client_id = credentials.get('client_id')
            self.client_secret = credentials.get('client_secret')

            if self.client_id is None:
                print("Visit: https://app.the-most.ai/integrations and get clientId, clientSecret")
                self.client_id = input("Please enter your client ID: ")
                self.client_secret = input("Please enter your client secret: ")
                self.save_credentials()
        else:
            self.save_credentials()

        self.session = httpx.AsyncClient()
        self.access_token = None
        self.model_id = model_id

    async def __aenter__(self):
        await self.session.__aenter__()
        await self.refresh_access_token()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.__aexit__(exc_type, exc_val, exc_tb)

    @property
    def cache_path(self):
        path = Path.home() / ".most"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def load_credentials(self):
        path = self.cache_path / "credentials.json"
        if not path.exists():
            return {}
        else:
            return json5.loads(path.read_text())

    def save_credentials(self):
        path = self.cache_path / "credentials.json"
        path.write_text(json5.dumps({
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }))

    def clone(self):
        client = AsyncMostClient(client_id=self.client_id,
                                 client_secret=self.client_secret,
                                 model_id=self.model_id)
        client.access_token = self.access_token
        client.session = self.session
        return client

    def with_model(self, model_id):
        client = self.clone()
        client.model_id = model_id
        return client

    async def refresh_access_token(self):
        resp = await self.session.post("https://api.the-most.ai/api/external/access_token",
                                       json={"client_id": self.client_id,
                                             "client_secret": self.client_secret})
        access_token = resp.json()
        self.access_token = access_token

    async def get(self, url, **kwargs):
        if self.access_token is None:
            await self.refresh_access_token()
        headers = kwargs.pop("headers", {})
        headers.update({"Authorization": "Bearer %s" % self.access_token})
        resp = await self.session.get(url,
                                      headers=headers,
                                      timeout=None,
                                      **kwargs)
        if resp.status_code == 401:
            await self.refresh_access_token()
            return await self.get(url,
                                  headers=headers,
                                  **kwargs)
        if resp.status_code >= 400:
            raise RuntimeError(resp.json()['message'] if resp.headers.get(
                "Content-Type") == "application/json" else "Something went wrong.")
        return resp

    async def post(self, url,
                   data=None,
                   json=None,
                   **kwargs):
        if self.access_token is None:
            await self.refresh_access_token()
        headers = kwargs.pop("headers", {})
        headers.update({"Authorization": "Bearer %s" % self.access_token})
        resp = await self.session.post(url,
                                       data=data,
                                       json=json,
                                       headers=headers,
                                       timeout=None,
                                       **kwargs)
        if resp.status_code == 401:
            await self.refresh_access_token()
            return await self.post(url,
                                   data=data,
                                   json=json,
                                   headers=headers,
                                   **kwargs)
        if resp.status_code >= 400:
            raise RuntimeError(resp.json()['message'] if resp.headers.get(
                "Content-Type") == "application/json" else "Something went wrong.")
        return resp

    async def upload_audio(self, audio_path) -> Audio:
        with open(audio_path, mode='rb') as f:
            resp = await self.post(f"https://api.the-most.ai/api/external/{self.client_id}/upload",
                                   files={"audio_file": f})
        return self.retort.load(resp.json(), Audio)

    async def upload_text(self, text: str) -> Text:
        resp = await self.post(f"https://api.the-most.ai/api/external/{self.client_id}/upload_text",
                               json={"text": text})
        return self.retort.load(resp.json(), Text)

    async def upload_audio_url(self, audio_url) -> Audio:
        resp = await self.post(f"https://api.the-most.ai/api/external/{self.client_id}/upload_url",
                               json={"audio_url": audio_url})
        return self.retort.load(resp.json(), Audio)

    async def list_audios(self,
                    offset: int = 0,
                    limit: int = 10) -> List[Audio]:
        resp = await self.get(f"https://api.the-most.ai/api/external/{self.client_id}/list?offset={offset}&limit={limit}")
        audio_list = resp.json()
        return self.retort.load(audio_list, List[Audio])

    async def get_model_script(self) -> Script:
        if self.model_id is None:
            raise RuntimeError("Please choose a model to apply. [try list_models()]")
        resp = await self.get(f"https://api.the-most.ai/api/external/{self.client_id}/model/{self.model_id}/script")
        return self.retort.load(resp.json(), Script)

    async def list_models(self):
        resp = await self.get("https://api.the-most.ai/api/external/list_models")
        return [self.with_model(model['model'])
                for model in resp.json()]

    async def apply(self, audio_id) -> Result:
        if self.model_id is None:
            raise RuntimeError("Please choose a model to apply. [try list_models()]")
        resp = await self.post(f"https://api.the-most.ai/api/external/{self.client_id}/audio/{audio_id}/model/{self.model_id}/apply")
        return self.retort.load(resp.json(), Result)

    async def apply_later(self, audio_id):
        if self.model_id is None:
            raise RuntimeError("Please choose a model to apply. [try list_models()]")
        resp = await self.post(f"https://api.the-most.ai/api/external/{self.client_id}/audio/{audio_id}/model/{self.model_id}/apply_async")
        return self.retort.load(resp.json(), Result)

    async def get_job_status(self, audio_id) -> JobStatus:
        if self.model_id is None:
            raise RuntimeError("Please choose a model to apply. [try list_models()]")
        resp = await self.post(f"https://api.the-most.ai/api/external/{self.client_id}/audio/{audio_id}/model/{self.model_id}/apply_status")
        return self.retort.load(resp.json(), JobStatus)

    async def fetch_results(self, audio_id) -> Result:
        if self.model_id is None:
            raise RuntimeError("Please choose a model to apply. [try list_models()]")

        resp = await self.get(f"https://api.the-most.ai/api/external/{self.client_id}/audio/{audio_id}/model/{self.model_id}/results")
        return self.retort.load(resp.json(), Result)

    async def fetch_text(self, audio_id) -> Result:
        if self.model_id is None:
            raise RuntimeError("Please choose a model to apply. [try list_models()]")

        resp = await self.get(f"https://api.the-most.ai/api/external/{self.client_id}/audio/{audio_id}/model/{self.model_id}/text")
        return self.retort.load(resp.json(), Result)

    async def export(self, audio_ids: List[str]) -> str:
        if self.model_id is None:
            raise RuntimeError("Please choose a model to apply. [try list_models()]")

        resp = await self.get(f"https://api.the-most.ai/api/external/{self.client_id}/model/{self.model_id}/export",
                              params={'audio_ids': ','.join(audio_ids)})
        return resp.next_request.url

    async def __call__(self, audio_path: Path):
        audio = await self.upload_audio(audio_path)
        return await self.apply(audio.id)

    def __repr__(self):
        return "<AsyncMostClient(model_id='%s')>" % (self.model_id, )
