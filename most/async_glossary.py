from typing import List

from .async_api import AsyncMostClient
from .types import GlossaryNGram


class AsyncGlossary(object):
    def __init__(self, client: AsyncMostClient):
        super(AsyncGlossary, self).__init__()
        self.client = client

    async def add_ngrams(self, ngrams: List[GlossaryNGram] | GlossaryNGram) -> List[GlossaryNGram]:
        if not isinstance(ngrams, list):
            ngrams = [ngrams]
        resp = await self.client.post(f"/{self.client.client_id}/upload_glossary",
                                      json=[ngram.to_dict() for ngram in ngrams])
        return self.client.retort.load(resp.json(), List[GlossaryNGram])

    async def list_ngrams(self) -> List[GlossaryNGram]:
        resp = await self.client.get(f"/{self.client.client_id}/glossary")
        return self.client.retort.load(resp.json(), List[GlossaryNGram])

    async def del_ngrams(self, ngram_ids: List[str] | str):
        if not isinstance(ngram_ids, list):
            ngram_ids = [ngram_ids]
        await self.client.post(f"/{self.client.client_id}/delete_glossary_ngrams",
                               json=ngram_ids)
        return self

    async def drop(self):
        await self.client.post(f"/{self.client.client_id}/delete_glossary")
        return self
