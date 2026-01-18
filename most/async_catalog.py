from typing import List, Optional

from .async_api import AsyncMostClient
from .types import Item


class AsyncCatalog(object):
    def __init__(self, client: AsyncMostClient):
        super(AsyncCatalog, self).__init__()
        self.client = client

    async def add_items(self, items: List[Item] | Item) -> List[Item]:
        if not isinstance(items, list):
            items = [items]
        resp = await self.client.post(f"/{self.client.client_id}/upload_items",
                                      json=[item.to_dict() for item in items])
        # return self.client.retort.load(resp.json(), List[Item])
        return [Item.from_dict(item)
                for item in resp.json()]

    async def list_items(self) -> List[Item]:
        resp = await self.client.get(f"/{self.client.client_id}/items")
        # return self.client.retort.load(resp.json(), List[Item])
        return [Item.from_dict(item)
                for item in resp.json()]

    async def delete_items(self, item_ids: List[str]):
        if not isinstance(item_ids, list):
            item_ids = [item_ids]
        await self.client.post(f"/{self.client.client_id}/delete_items",
                               json=item_ids)
        return self

    async def drop(self):
        await self.client.post(f"/{self.client.client_id}/items/drop")
        return self

    async def search_items(self,
                           query: str,

                           min_price: Optional[int] = None,
                           max_price: Optional[int] = None,
                           category: Optional[str] = None,

                           only_available: bool = False,

                           limit: int = 10) -> List[Item]:

        params = {
            "query": query,
            "limit": limit,
            "only_available": only_available,
        }
        if min_price is not None:
            params["min_price"] = min_price
        if max_price is not None:
            params["max_price"] = max_price
        if category is not None:
            params["category"] = category

        resp = await self.client.get(f"/{self.client.client_id}/search_items",
                                     params=params)
        # return self.client.retort.load(resp.json(), List[Item])
        return [Item.from_dict(item)
                for item in resp.json()]

    async def search_items_by_photo(self, image_url: str,

                                    min_price: Optional[int] = None,
                                    max_price: Optional[int] = None,
                                    category: Optional[str] = None,

                                    only_available: bool = False,

                                    limit: int = 10) -> List[Item]:
        params = {
            "image_url": image_url,
            "limit": limit,
            "only_available": only_available,
        }
        if min_price is not None:
            params["min_price"] = min_price
        if max_price is not None:
            params["max_price"] = max_price
        if category is not None:
            params["category"] = category

        resp = await self.client.get(f"/{self.client.client_id}/search_items_by_photo",
                                     params=params)
        # return self.client.retort.load(resp.json(), List[Item])
        return [Item.from_dict(item)
                for item in resp.json()]
