from .api import MostClient


class Teleprompter:
    def __init__(self, client: MostClient):
        self.client = client

    def train(self, audio_id: str):
        pass

    def suggest(self, phrase: str):
        pass
