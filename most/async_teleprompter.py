from .async_api import AsyncMostClient


class AsyncTeleprompter:
    def __init__(self, client: AsyncMostClient):
        self.client = client

    async def train(self, audio_id: str,
                    client_speaker: str):
        resp = await self.client.post(f"/teleprompter/{self.client.client_id}/train",
                                     json={
                                         "audio_id": audio_id,
                                         "client_speaker": client_speaker
                                     })
        if resp.status_code >= 400:
            raise RuntimeError("Audio can't be indexed")
        return resp.json()

    async def suggest(self, phrase: str):
        resp = await self.client.get(f"/teleprompter/{self.client.client_id}/prompt",
                                     params={
                                         "phrase": phrase
                                     })
        if resp.status_code >= 400:
            raise RuntimeError("Audio can't be indexed")
        return resp.json()

    async def drop(self):
        resp = await self.client.post(f"/teleprompter/{self.client.client_id}/drop")
        if resp.status_code >= 400:
            raise RuntimeError("Audio can't be indexed")
        return resp.json()
