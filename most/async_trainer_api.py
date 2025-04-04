from typing import List

from . import AsyncMostClient
from .types import HumanFeedback


class AsyncTrainer(object):
    def __init__(self, client: AsyncMostClient):
        super(AsyncTrainer, self).__init__()
        self.client = client
        if self.client.model_id is None:
            raise RuntimeError("Train must be implemented for stable model_id")

    async def fit(self, data: List[HumanFeedback]):
        resp = await self.client.put(f"/{self.client.client_id}/model/{self.client.model_id}/data",
                                     json={"data": [hf.to_dict() for hf in data]})
        return self

    async def evaluate(self, data: List[HumanFeedback]):
        gt_data = await self.get_data_points()
        return HumanFeedback.calculate_accuracy(data, gt_data)

    async def get_data_points(self) -> List[HumanFeedback]:
        resp = await self.client.get(f"/{self.client.client_id}/model/{self.client.model_id}/data")
        audio_list = resp.json()
        return self.client.retort.load(audio_list, List[HumanFeedback])
