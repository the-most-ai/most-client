from pathlib import Path

import json5
import requests
from adaptix import Retort
from most.types import Audio
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
                                        "client_secret": self.client_secret})
        access_token = resp.json()
        self.access_token = access_token

    def get(self, url, **kwargs):
        if self.access_token is None:
            self.refresh_access_token()
        headers = kwargs.pop("headers", {})
        headers.update({"Authorization": "Bearer %s" % self.access_token})
        resp = self.session.get(url,
                                headers=headers,
                                **kwargs)
        if resp.status_code == 401:
            self.refresh_access_token()
            return self.get(url,
                            headers=headers,
                            **kwargs)
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
                                 **kwargs)
        if resp.status_code == 401:
            self.refresh_access_token()
            return self.post(url,
                             data=data,
                             json=json,
                             headers=headers,
                             **kwargs)
        return resp

    def upload_audio(self, audio_path) -> Audio:
        with open(audio_path, 'rb') as f:
            resp = self.post(f"https://api.the-most.ai/api/external/{self.client_id}/upload",
                             files={"audio_file": f})
        return self.retort.load(resp.json(), Audio)

    def list_audios(self, limit: int = 10):
        pass

    def list_models(self):
        resp = self.get("https://api.the-most.ai/api/external/list_models")
        return [self.with_model(model['model'])
                for model in resp.json()]

    def fetch_results(self, model_id, audio_id):
        pass

    def __repr__(self):
        return "<MostClient(model_id='%s')>" % (self.model_id, )
