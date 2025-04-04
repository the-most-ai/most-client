from typing import List
from .api import MostClient
from .types import HumanFeedback


class Trainer(object):
    def __init__(self, client: MostClient):
        super(Trainer, self).__init__()
        self.client = client
        if self.client.model_id is None:
            raise RuntimeError("Train must be implemented for stable model_id")

    def fit(self, data: List[HumanFeedback]):
        resp = self.client.put(f"/{self.client.client_id}/model/{self.client.model_id}/data",
                               json={"data": [hf.to_dict() for hf in data]})
        return self

    def evaluate(self, data: List[HumanFeedback]):
        gt_data = self.get_data_points()
        return HumanFeedback.calculate_accuracy(data, gt_data)

    def get_data_points(self) -> List[HumanFeedback]:
        resp = self.client.get(f"/{self.client.client_id}/model/{self.client.model_id}/data")
        audio_list = resp.json()
        return self.client.retort.load(audio_list, List[HumanFeedback])
