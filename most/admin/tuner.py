from typing import Literal

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

    def with_client(self, client: MostClient):
        return Tuner(client, self.username, self.password)

    def get_model_info(self):
        resp = self.client.get(
            self.admin_base_url + f"/{self.client.client_id}/model/{self.client.model_id}/card",
            headers={
                "X-API-KEY": f"{self.username}:{self.password}"
            }
        )

        resp.raise_for_status()
        resp = resp.json()
        return resp

    def list_transcribers(self):
        resp = self.client.get(
            self.admin_base_url + f"/transcribers/list",
            headers={
                "X-API-KEY": f"{self.username}:{self.password}"
            }
        )
        resp.raise_for_status()
        return resp.json()

    def list_llms(self):
        resp = self.client.get(
            self.admin_base_url + f"/llms/list",
            headers={
                "X-API-KEY": f"{self.username}:{self.password}"
            }
        )
        resp.raise_for_status()
        return resp.json()

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

    def list_production_clients(self):
        resp = self.client.get(
            self.admin_base_url + f"/models/list",
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

    def delete_model(self, model_id: str):
        resp = self.client.post(
            self.admin_base_url + f"/{self.client.client_id}/model/{model_id}/delete",
            headers={
                "X-API-KEY": f"{self.username}:{self.password}"
            }
        )

        resp.raise_for_status()
        return resp.json()

    def get_cost(self, data_id: str,
                 data_source: Literal["text", "audio"] = "audio"):
        resp = self.client.get(
            self.admin_base_url + f"/{self.client.client_id}/model/{self.client.model_id}/{data_source}/{data_id}/cost",
            headers={
                "X-API-KEY": f"{self.username}:{self.password}"
            }
        )
        return resp.json()
