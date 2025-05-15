from typing import List

from .async_api import AsyncMostClient
from .types import GlossaryNGram


class AsyncGlossary(object):
    def __init__(self, client: AsyncMostClient):
        self.client = client

    async def add_ngram(self, ngram: GlossaryNGram):
        pass

    async def list_ngrams(self) -> List[GlossaryNGram]:
        return []

    async def del_ngram(self, ngram_id: str):
        pass
