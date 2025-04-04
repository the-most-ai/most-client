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
        raise NotImplementedError()

    async def evaluate(self, data: List[HumanFeedback]):
        raise NotImplementedError()

    async def get_data_points(self) -> List[HumanFeedback]:
        raise NotImplementedError()
