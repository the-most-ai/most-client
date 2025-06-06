from typing import List

from .api import MostClient
from .types import GlossaryNGram


class Glossary(object):
    def __init__(self, client: MostClient):
        super(Glossary, self).__init__()
        self.client = client

    def add_ngrams(self, ngrams: List[GlossaryNGram] | GlossaryNGram) -> List[GlossaryNGram]:
        if not isinstance(ngrams, list):
            ngrams = [ngrams]
        resp = self.client.post(f"/{self.client.client_id}/upload_glossary",
                                json=[ngram.to_dict() for ngram in ngrams])
        return self.client.retort.load(resp.json(), List[GlossaryNGram])

    def list_ngrams(self) -> List[GlossaryNGram]:
        resp = self.client.get(f"/{self.client.client_id}/glossary")
        return self.client.retort.load(resp.json(), List[GlossaryNGram])

    def del_ngrams(self, ngram_ids: List[str] | str):
        if not isinstance(ngram_ids, list):
            ngram_ids = [ngram_ids]
        self.client.post(f"/{self.client.client_id}/delete_glossary_ngrams",
                         json=ngram_ids)
        return self

    def drop(self):
        self.client.post(f"/{self.client.client_id}/delete_glossary")
        return self
