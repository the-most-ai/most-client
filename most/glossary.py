from typing import List

from .api import MostClient
from .types import GlossaryNGram


class Glossary(object):
    def __init__(self, client: MostClient):
        self.client = client

    def add_ngram(self, ngram: GlossaryNGram):
        pass

    def list_ngrams(self) -> List[GlossaryNGram]:
        return []

    def del_ngram(self, ngram_id: str):
        pass
