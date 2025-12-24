from .api import MostClient


class Teleprompter:
    def __init__(self, client: MostClient):
        self.client = client

    def train(self, audio_id: str,
                    client_speaker: str):
        resp = self.client.post(f"/teleprompter/{self.client.client_id}/train",
                                json={
                                    "audio_id": audio_id,
                                     "client_speaker": client_speaker
                                })
        if resp.status_code >= 400:
            raise RuntimeError("Audio can't be indexed")
        return resp.json()

    def suggest(self, phrase: str):
        resp = self.client.get(f"/teleprompter/{self.client.client_id}/prompt",
                               params={
                                   "phrase": phrase
                               })
        if resp.status_code >= 400:
            raise RuntimeError("Audio can't be indexed")
        return resp.json()

    def drop(self):
        resp = self.client.post(f"/teleprompter/{self.client.client_id}/drop")
        if resp.status_code >= 400:
            raise RuntimeError("Audio can't be indexed")
        return resp.json()
