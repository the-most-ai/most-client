from typing import List, Dict
import json5
import requests
from adaptix import Retort
from most.types import Audio, Result, Script, JobStatus, Text, StoredAudioData, is_valid_id
from pathlib import Path


class MostClient(object):
    retort = Retort()

    def __init__(self,
                 client_id=None,
                 client_secret=None,
                 model_id=None):
        super(MostClient, self).__init__()
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

        self.session = requests.Session()
        self.access_token = None
        self.model_id = model_id

        self.refresh_access_token()

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
        client = MostClient(client_id=self.client_id,
                            client_secret=self.client_secret,
                            model_id=self.model_id)
        client.access_token = self.access_token
        client.session = self.session
        return client

    def with_model(self, model_id):
        client = self.clone()
        client.model_id = model_id
        return client

    def refresh_access_token(self):
        resp = self.session.post("https://api.the-most.ai/api/external/access_token",
                                 json={"client_id": self.client_id,
                                        "client_secret": self.client_secret},
                                 timeout=None)
        access_token = resp.json()
        self.access_token = access_token

    def get(self, url, **kwargs):
        if self.access_token is None:
            self.refresh_access_token()
        headers = kwargs.pop("headers", {})
        headers.update({"Authorization": "Bearer %s" % self.access_token})
        resp = self.session.get(url,
                                headers=headers,
                                timeout=None,
                                **kwargs)
        if resp.status_code == 401:
            self.refresh_access_token()
            return self.get(url,
                            headers=headers,
                            **kwargs)
        if resp.status_code >= 400:
            raise RuntimeError(resp.json()['message'] if resp.headers.get("Content-Type") == "application/json" else "Something went wrong.")
        return resp

    def post(self, url,
             data=None,
             json=None,
             **kwargs):
        if self.access_token is None:
            self.refresh_access_token()
        headers = kwargs.pop("headers", {})
        headers.update({"Authorization": "Bearer %s" % self.access_token})
        resp = self.session.post(url,
                                 data=data,
                                 json=json,
                                 headers=headers,
                                 timeout=None,
                                 **kwargs)
        if resp.status_code == 401:
            self.refresh_access_token()
            return self.post(url,
                             data=data,
                             json=json,
                             headers=headers,
                             **kwargs)
        if resp.status_code >= 400:
            raise RuntimeError(resp.json()['message'] if resp.headers.get("Content-Type") == "application/json" else "Something went wrong.")
        return resp

    def upload_text(self, text: str) -> Text:
        resp = self.post(f"https://api.the-most.ai/api/external/{self.client_id}/upload_text",
                         files={"text": text})
        return self.retort.load(resp.json(), Text)

    def upload_audio(self, audio_path) -> Audio:
        with open(audio_path, 'rb') as f:
            resp = self.post(f"https://api.the-most.ai/api/external/{self.client_id}/upload",
                             files={"audio_file": f})
        return self.retort.load(resp.json(), Audio)

    def upload_audio_url(self, audio_url) -> Audio:
        resp = self.post(f"https://api.the-most.ai/api/external/{self.client_id}/upload_url",
                         json={"audio_url": audio_url})
        return self.retort.load(resp.json(), Audio)

    def list_audios(self,
                    offset: int = 0,
                    limit: int = 10) -> List[Audio]:
        resp = self.get(f"https://api.the-most.ai/api/external/{self.client_id}/list?offset={offset}&limit={limit}")
        audio_list = resp.json()
        return self.retort.load(audio_list, List[Audio])

    def get_model_script(self) -> Script:
        if not is_valid_id(self.model_id):
            raise RuntimeError("Please choose valid model to apply. [try list_models()]")

        resp = self.get(f"https://api.the-most.ai/api/external/{self.client_id}/model/{self.model_id}/script")
        return self.retort.load(resp.json(), Script)

    def list_models(self):
        resp = self.get("https://api.the-most.ai/api/external/list_models")
        return [self.with_model(model['model'])
                for model in resp.json()]

    def apply(self, audio_id) -> Result:
        if not is_valid_id(self.model_id):
            raise RuntimeError("Please choose valid model to apply. [try list_models()]")

        if not is_valid_id(audio_id):
            raise RuntimeError("Please use valid audio_id. [try audio.id from list_audios()]")

        resp = self.post(f"https://api.the-most.ai/api/external/{self.client_id}/audio/{audio_id}/model/{self.model_id}/apply")
        return self.retort.load(resp.json(), Result)

    def apply_later(self, audio_id) -> Result:
        if not is_valid_id(self.model_id):
            raise RuntimeError("Please choose valid model to apply. [try list_models()]")

        if not is_valid_id(audio_id):
            raise RuntimeError("Please use valid audio_id. [try audio.id from list_audios()]")

        resp = self.post(f"https://api.the-most.ai/api/external/{self.client_id}/audio/{audio_id}/model/{self.model_id}/apply_async")
        return self.retort.load(resp.json(), Result)

    def get_job_status(self, audio_id) -> JobStatus:
        if not is_valid_id(self.model_id):
            raise RuntimeError("Please choose valid model to apply. [try list_models()]")

        if not is_valid_id(audio_id):
            raise RuntimeError("Please use valid audio_id. [try audio.id from list_audios()]")

        resp = self.post(f"https://api.the-most.ai/api/external/{self.client_id}/audio/{audio_id}/model/{self.model_id}/apply_status")
        return self.retort.load(resp.json(), JobStatus)

    def fetch_results(self, audio_id) -> Result:
        if not is_valid_id(self.model_id):
            raise RuntimeError("Please choose valid model to apply. [try list_models()]")

        if not is_valid_id(audio_id):
            raise RuntimeError("Please use valid audio_id. [try audio.id from list_audios()]")

        resp = self.get(f"https://api.the-most.ai/api/external/{self.client_id}/audio/{audio_id}/model/{self.model_id}/results")
        return self.retort.load(resp.json(), Result)

    def fetch_text(self, audio_id: str) -> Result:
        if not is_valid_id(self.model_id):
            raise RuntimeError("Please choose valid model to apply. [try list_models()]")

        if not is_valid_id(audio_id):
            raise RuntimeError("Please use valid audio_id. [try audio.id from list_audios()]")

        resp = self.get(f"https://api.the-most.ai/api/external/{self.client_id}/audio/{audio_id}/model/{self.model_id}/text")
        return self.retort.load(resp.json(), Result)

    def export(self, audio_ids: List[str]) -> str:
        if not is_valid_id(self.model_id):
            raise RuntimeError("Please choose valid model to apply. [try list_models()]")

        resp = self.get(f"https://api.the-most.ai/api/external/{self.client_id}/model/{self.model_id}/export",
                        params={'audio_ids': ','.join(audio_ids)})
        return resp.url

    def store_info(self,
                   audio_id: str,
                   data: Dict[str, str]):
        if not is_valid_id(audio_id):
            raise RuntimeError("Please use valid audio_id. [try audio.id from list_audios()]")

        resp = self.post(f"https://api.the-most.ai/api/external/{self.client_id}/audio/{audio_id}/info",
                         json={
                             "data": data,
                         })
        return self.retort.load(resp.json(), StoredAudioData)

    def fetch_info(self, audio_id: str) -> Dict[str, str]:
        if not is_valid_id(audio_id):
            raise RuntimeError("Please use valid audio_id. [try audio.id from list_audios()]")

        resp = self.get(f"https://api.the-most.ai/api/external/{self.client_id}/audio/{audio_id}/info")
        return self.retort.load(resp.json(), StoredAudioData)

    def __call__(self, audio_path: Path):
        audio = self.upload_audio(audio_path)
        return self.apply(audio.id)

    def __repr__(self):
        return "<MostClient(model_id='%s')>" % (self.model_id, )
