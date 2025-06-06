from typing import List

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
        return self.client.retort.load(resp.json(), List[Item])

    def list_items(self) -> List[Item]:
        resp = self.client.get(f"/{self.client.client_id}/items")
        return self.client.retort.load(resp.json(), List[Item])

    def delete_items(self, item_ids: List[str]):
        if not isinstance(item_ids, list):
            item_ids = [item_ids]
        self.client.post(f"/{self.client.client_id}/delete_items",
                         json=item_ids)
        return self
