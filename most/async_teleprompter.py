from .async_api import AsyncMostClient


class AsyncTeleprompter:
    def __init__(self, client: AsyncMostClient):
        self.client = client

    async def train(self, audio_id: str):
        pass

    async def suggest(self, phrase: str):
        pass
