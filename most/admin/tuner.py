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

    def list_clients(self):
        resp = self.client.get(
            self.admin_base_url + f"/list",
            headers={
                "X-API-KEY": f"{self.username}:{self.password}"
            }
        )
        resp.raise_for_status()
        return [MostClient(**credentials)
                for credentials in resp.json()]

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

    def clone_model(self,
                    model_name: str,
                    transcribator_name: str,
                    llm_name: str):
        resp = self.client.post(
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
