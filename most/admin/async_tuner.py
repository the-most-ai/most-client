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
