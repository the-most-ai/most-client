from typing import List

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
        return self.client.retort.load(resp.json(), List[Item])

    async def list_items(self) -> List[Item]:
        resp = await self.client.get(f"/{self.client.client_id}/items")
        return self.client.retort.load(resp.json(), List[Item])

    async def delete_items(self, item_ids: List[str]):
        if not isinstance(item_ids, list):
            item_ids = [item_ids]
        await self.client.post(f"/{self.client.client_id}/delete_items",
                               json=item_ids)
        return self
