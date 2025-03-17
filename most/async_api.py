import io
import os
import uuid
from pathlib import Path
from typing import Dict, List, Optional

import httpx
import json5
from adaptix import Retort
from pydub import AudioSegment

from most.score_calculation import ScoreCalculation
from most.types import (
    Audio,
    DialogResult,
    JobStatus,
    Result,
    Script,
    StoredAudioData,
    Text,
    is_valid_id, SearchParams, ScriptScoreMapping, Dialog,
)


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
        self.score_modifier: Optional[ScoreCalculation] = None

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
        client.score_modifier = self.score_modifier
        return client

    def with_model(self, model_id):
        client = self.clone()
        if not is_valid_id(self.model_id):
            raise RuntimeError("Please choose valid model to apply. [try list_models()]")
        client.model_id = model_id
        client.score_modifier = None
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

    async def upload_audio_segment(self, audio: AudioSegment,
                                   audio_name: Optional[str] = None) -> Audio:
        f = io.BytesIO()
        audio.export(f, format="mp3")
        f.seek(0)
        if audio_name is None:
            audio_name = uuid.uuid4().hex + ".mp3"
        resp = await self.post(f"https://api.the-most.ai/api/external/{self.client_id}/upload",
                               files={"audio_file": (audio_name, f, 'audio/mp3')})
        return self.retort.load(resp.json(), Audio)

    async def upload_text(self, text: str) -> Text:
        resp = await self.post(f"https://api.the-most.ai/api/external/{self.client_id}/upload_text",
                               json={"text": text})
        return self.retort.load(resp.json(), Text)

    async def upload_dialog(self, dialog: Dialog) -> DialogResult:
        resp = await self.post(f"https://api.the-most.ai/api/external/{self.client_id}/upload_dialog",
                               json={"dialog": dialog})
        return self.retort.load(resp.json(), DialogResult)

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

    async def list_texts(self,
                         offset: int = 0,
                         limit: int = 10) -> List[Text]:
        resp = await self.get(f"https://api.the-most.ai/api/external/{self.client_id}/list_texts?offset={offset}&limit={limit}")
        texts_list = resp.json()
        return self.retort.load(texts_list, List[Text])

    async def get_model_script(self) -> Script:
        if not is_valid_id(self.model_id):
            raise RuntimeError("Please choose valid model to apply. [try list_models()]")

        resp = await self.get(f"https://api.the-most.ai/api/external/{self.client_id}/model/{self.model_id}/script")
        return self.retort.load(resp.json(), Script)

    async def get_score_modifier(self):
        if self.score_modifier is None:
            if not is_valid_id(self.model_id):
                raise RuntimeError("Please choose valid model to apply. [try list_models()]")

            resp = await self.get(f"https://api.the-most.ai/api/external/{self.client_id}/model/{self.model_id}/score_mapping")
            score_mapping = self.retort.load(resp.json(), List[ScriptScoreMapping])
            self.score_modifier = ScoreCalculation(score_mapping)
        return self.score_modifier

    async def list_models(self):
        resp = await self.get("https://api.the-most.ai/api/external/list_models")
        return [self.with_model(model['model'])
                for model in resp.json()]

    async def apply(self, audio_id,
                    modify_scores: bool = False) -> Result:
        if not is_valid_id(self.model_id):
            raise RuntimeError("Please choose valid model to apply. [try list_models()]")

        if not is_valid_id(audio_id):
            raise RuntimeError("Please use valid audio_id. [try audio.id from list_audios()]")

        resp = await self.post(f"https://api.the-most.ai/api/external/{self.client_id}/audio/{audio_id}/model/{self.model_id}/apply")
        result = self.retort.load(resp.json(), Result)
        if modify_scores:
            result = self.score_modifier.modify(result)
        return result

    async def apply_on_text(self, text_id,
                            modify_scores: bool = False) -> Result:
        if not is_valid_id(self.model_id):
            raise RuntimeError("Please choose valid model to apply. [try list_models()]")

        if not is_valid_id(text_id):
            raise RuntimeError("Please use valid text_id. [try text.id from list_texts()]")

        resp = await self.post(f"https://api.the-most.ai/api/external/{self.client_id}/text/{text_id}/model/{self.model_id}/apply")
        result = self.retort.load(resp.json(), Result)
        if modify_scores:
            result = self.score_modifier.modify(result)
        return result

    async def apply_later(self, audio_id,
                          modify_scores: bool = False) -> Result:
        if not is_valid_id(self.model_id):
            raise RuntimeError("Please choose valid model to apply. [try list_models()]")

        if not is_valid_id(audio_id):
            raise RuntimeError("Please use valid audio_id. [try audio.id from list_audios()]")

        resp = await self.post(f"https://api.the-most.ai/api/external/{self.client_id}/audio/{audio_id}/model/{self.model_id}/apply_async")
        result = self.retort.load(resp.json(), Result)
        if modify_scores:
            result = self.score_modifier.modify(result)
        return result

    async def apply_on_text_later(self, text_id,
                                  modify_scores: bool = False) -> Result:
        if not is_valid_id(self.model_id):
            raise RuntimeError("Please choose valid model to apply. [try list_models()]")

        if not is_valid_id(text_id):
            raise RuntimeError("Please use valid text_id. [try audio.id from list_texts()]")

        resp = await self.post(f"https://api.the-most.ai/api/external/{self.client_id}/text/{text_id}/model/{self.model_id}/apply_async")
        result = self.retort.load(resp.json(), Result)
        if modify_scores:
            result = self.score_modifier.modify(result)
        return result

    async def get_job_status(self, audio_id) -> JobStatus:
        if not is_valid_id(self.model_id):
            raise RuntimeError("Please choose valid model to apply. [try list_models()]")

        if not is_valid_id(audio_id):
            raise RuntimeError("Please use valid audio_id. [try audio.id from list_audios()]")

        resp = await self.post(f"https://api.the-most.ai/api/external/{self.client_id}/audio/{audio_id}/model/{self.model_id}/apply_status")
        return self.retort.load(resp.json(), JobStatus)

    async def fetch_results(self, audio_id,
                            modify_scores: bool = False) -> Result:
        if not is_valid_id(self.model_id):
            raise RuntimeError("Please choose valid model to apply. [try list_models()]")

        if not is_valid_id(audio_id):
            raise RuntimeError("Please use valid audio_id. [try audio.id from list_audios()]")

        resp = await self.get(f"https://api.the-most.ai/api/external/{self.client_id}/audio/{audio_id}/model/{self.model_id}/results")
        result = self.retort.load(resp.json(), Result)
        if modify_scores:
            result = self.score_modifier.modify(result)
        return result

    async def fetch_text(self, audio_id) -> Result:
        if not is_valid_id(self.model_id):
            raise RuntimeError("Please choose valid model to apply. [try list_models()]")

        if not is_valid_id(audio_id):
            raise RuntimeError("Please use valid audio_id. [try audio.id from list_audios()]")

        resp = await self.get(f"https://api.the-most.ai/api/external/{self.client_id}/audio/{audio_id}/model/{self.model_id}/text")
        return self.retort.load(resp.json(), Result)

    async def fetch_dialog(self, audio_id) -> DialogResult:
        if not is_valid_id(self.model_id):
            raise RuntimeError("Please choose valid model to apply. [try list_models()]")

        if not is_valid_id(audio_id):
            raise RuntimeError("Please use valid audio_id. [try audio.id from list_audios()]")

        resp = await self.get(f"https://api.the-most.ai/api/external/{self.client_id}/audio/{audio_id}/model/{self.model_id}/dialog")
        return self.retort.load(resp.json(), DialogResult)

    async def export(self, audio_ids: List[str],
                     aggregated_by: Optional[str] = None,
                     aggregation_title: Optional[str] = None) -> str:
        if aggregation_title is None:
            aggregation_title = aggregated_by

        if not is_valid_id(self.model_id):
            raise RuntimeError("Please choose valid model to apply. [try list_models()]")

        resp = await self.get(f"https://api.the-most.ai/api/external/{self.client_id}/model/{self.model_id}/export",
                              params={'audio_ids': ','.join(audio_ids),
                                      "aggregated_by": aggregated_by,
                                      "aggregation_title": aggregation_title})
        return resp.next_request.url

    async def store_info(self,
                         audio_id: str,
                         data: Dict[str, str]):
        resp = await self.post(f"https://api.the-most.ai/api/external/{self.client_id}/audio/{audio_id}/info",
                               json={
                                   "data": data,
                               })
        return self.retort.load(resp.json(), StoredAudioData)

    async def fetch_info(self, audio_id: str) -> Dict[str, str]:
        if not is_valid_id(audio_id):
            raise RuntimeError("Please use valid audio_id. [try audio.id from list_audios()]")
        resp = await self.get(f"https://api.the-most.ai/api/external/{self.client_id}/audio/{audio_id}/info")
        return self.retort.load(resp.json(), StoredAudioData)

    async def __call__(self, audio_path: Path,
                       modify_scores: bool = False) -> Result:
        audio = await self.upload_audio(audio_path)
        return await self.apply(audio.id,
                                modify_scores=modify_scores)

    def __repr__(self):
        return "<AsyncMostClient(model_id='%s')>" % (self.model_id, )

    async def get_audio_segment_by_url(self, audio_url,
                                       format=None):
        if format is None:
            format = os.path.splitext(audio_url)[1]
            format = format.strip().lower()

        resp = await self.session.get(audio_url,
                                      timeout=None)
        if resp.status_code >= 400:
            raise RuntimeError("Audio url is not accessable")

        audio = AudioSegment.from_file(io.BytesIO(resp.content),
                                       format=format)
        return audio

    async def index_audio(self, audio_id: str) -> None:
        resp = await self.post(f"https://api.the-most.ai/api/external/{self.client_id}/audio/{audio_id}/model/{self.model_id}/indexing")
        if resp.status_code >= 400:
            raise RuntimeError("Audio can't be indexed")
        return None

    async def search(self,
                     query: str,
                     filter: SearchParams,
                     limit: int = 10) -> List[Audio]:
        resp = await self.post(f"https://api.the-most.ai/api/external/{self.client_id}/model/{self.model_id}/search",
                               json={
                                   "query": query,
                                   "filter": filter.to_dict(),
                                   "limit": limit,
                               })
        if resp.status_code >= 400:
            raise RuntimeError("Audio can't be indexed")
        audio_list = resp.json()
        return self.retort.load(audio_list, List[Audio])
