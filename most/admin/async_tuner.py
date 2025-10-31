from typing import Literal

from ..async_api import AsyncMostClient


class AsyncTuner(object):
    def __init__(self,
                 client: AsyncMostClient,
                 username: str,
                 password: str):
        super(AsyncTuner, self).__init__()
        self.client = client
        self.admin_base_url = f"https://api.the-most.ai/api/admin"
        self.username = username
        self.password = password

    async def list_clients(self):
        resp = await self.client.get(
            self.admin_base_url + f"/list",
            headers={
                "X-API-KEY": f"{self.username}:{self.password}"
            }
        )
        resp.raise_for_status()
        return [AsyncMostClient(**credentials)
                for credentials in resp.json()]

    async def submit(self,
                     column: str,
                     subcolumn: str,
                     prompt: str,
                     model_name: str,
                     apply_type: str):
        resp = await self.client.post(
            self.admin_base_url + f"/{self.client.client_id}/model/{self.client.model_id}/submit",
            json={
                "submission": {
                "column": column,
                "subcolumn": subcolumn,
                "prompt": prompt,
                "model_name": model_name,
                "apply_type": apply_type
            }},
            headers={
                "X-API-KEY": f"{self.username}:{self.password}"
            }
        )

        resp.raise_for_status()
        return resp.json()

    async def clone_model(self,
                          model_name: str,
                          transcribator_name: str,
                          llm_name: str):
        resp = await self.client.post(
            self.admin_base_url + f"/{self.client.client_id}/model/{self.client.model_id}/clone",
            json={
                "model_name": model_name,
                "transcribator_name": transcribator_name,
                "llm_name": llm_name,
            },
            headers={
                "X-API-KEY": f"{self.username}:{self.password}"
            }
        )

        resp.raise_for_status()
        resp = resp.json()
        if "model" not in resp:
            raise Exception(f"Failed to clone model: {resp['message']}")
        return self.client.with_model(resp["model"])

    async def get_cost(self, data_id: str,
                       data_source: Literal["text", "audio"] = "audio"):
        resp = await self.client.get(
            self.admin_base_url + f"/{self.client.client_id}/model/{self.client.model_id}/{data_source}/{data_id}/cost",
            headers={
                "X-API-KEY": f"{self.username}:{self.password}"
            }
        )
        return resp.json()
