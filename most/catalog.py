from typing import List, Optional

from .api import MostClient
from .types import Item


class Catalog(object):
    def __init__(self, client: MostClient):
        super(Catalog, self).__init__()
        self.client = client

    def add_items(self, items: List[Item] | Item) -> List[Item]:
        if not isinstance(items, list):
            items = [items]
        resp = self.client.post(f"/{self.client.client_id}/upload_items",
                                json=[item.to_dict() for item in items])
        # return self.client.retort.load(resp.json(), List[Item])
        return [Item.from_dict(item)
                for item in resp.json()]

    def list_items(self) -> List[Item]:
        resp = self.client.get(f"/{self.client.client_id}/items")
        # return self.client.retort.load(resp.json(), List[Item])
        return [Item.from_dict(item)
                for item in resp.json()]

    def delete_items(self, item_ids: List[str]):
        if not isinstance(item_ids, list):
            item_ids = [item_ids]
        self.client.post(f"/{self.client.client_id}/delete_items",
                         json=item_ids)
        return self

    def drop(self):
        self.client.post(f"/{self.client.client_id}/items/drop")
        return self

    def search_items(self,
                     query: str,

                     min_price: Optional[int] = None,
                     max_price: Optional[int] = None,
                     category: Optional[str] = None,

                     limit: int = 10) -> List[Item]:
        resp = self.client.get(f"/{self.client.client_id}/search_items",
                               params={
                                   "query": query,

                                   "min_price": min_price,
                                   "max_price": max_price,
                                   "category": category,

                                   "limit": limit,
                               })
        # return self.client.retort.load(resp.json(), List[Item])
        return [Item.from_dict(item)
                for item in resp.json()]

    def search_items_by_photo(self, image_url: str) -> List[Item]:
        return []
