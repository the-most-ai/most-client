from typing import List, Literal, Optional
from . import AsyncMostClient
from .types import Audio
from .search_types import SearchParams


class AsyncMostSearcher(object):
    def __init__(self, client: AsyncMostClient,
                 data_source: Literal["text", "audio"]):
        self.client = client
        self.data_source = data_source

    async def count(self,
                    filter: Optional[SearchParams] = None):
        if filter is None:
            filter = SearchParams()

        resp = await self.client.get(f"/{self.client.client_id}/{self.data_source}/count",
                                     params={
                                         "filter": filter.to_json(),
                                     })
        if resp.status_code >= 400:
            raise RuntimeError("Audio can't be indexed")
        return resp.json()


    async def distinct(self,
                       key: str,
                       filter: Optional[SearchParams] = None) -> List[str]:
        """
        Distinct values of key.
        :param key: key should be stored in info (fetch_info, store_info)
        :return:
        """
        if filter is None:
            filter = SearchParams()
        resp = await self.client.get(f"/{self.client.client_id}/{self.data_source}/distinct",
                               params={"filter": filter.to_json(),
                                       "key": key})
        if resp.status_code >= 400:
            raise RuntimeError("Key is not valid")
        return resp.json()

    async def search(self,
                     filter: Optional[SearchParams] = None,
                     limit: int = 10) -> List[Audio]:
        if filter is None:
            filter = SearchParams()
        resp = await self.client.get(f"/{self.client.client_id}/{self.data_source}/search",
                                     params={
                                         "filter": filter.to_json(),
                                         "limit": limit,
                                     })
        if resp.status_code >= 400:
            raise RuntimeError("Audio can't be indexed")
        audio_list = resp.json()
        return self.client.retort.load(audio_list, List[Audio])
