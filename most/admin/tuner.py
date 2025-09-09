from ..api import MostClient


class Tuner(object):
    def __init__(self,
                 client: MostClient,
                 username: str,
                 password: str):
        super(Tuner, self).__init__()
        self.client = client
        self.admin_base_url = f"https://api.the-most.ai/api/admin"
        self.username = username
        self.password = password

    def submit(self,
               column: str,
               subcolumn: str,
               prompt: str,
               model_name: str,
               apply_type: str):
        resp = self.client.post(
            self.admin_base_url + f"/{self.client.client_id}/model/{self.client.model_id}/submit",
            json={
                "column": column,
                "subcolumn": subcolumn,
                "prompt": prompt,
                "model_name": model_name,
                "apply_type": apply_type
            },
            headers={
                "X-API-KEY": f"{self.username}:{self.password}"
            }
        )

        resp.raise_for_status()
        return resp.json()
