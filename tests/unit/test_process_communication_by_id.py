from unittest.mock import Mock
import pytest
import httpx

from most.api import MostClient
from most.types import ProcessCommunicationByIdResponse


@pytest.fixture
def mock_client(monkeypatch):
    """Клиент с мокированной HTTP-сессией для ETL API."""
    def mock_refresh_token(self):
        self.access_token = "test_token"

    monkeypatch.setattr(MostClient, "refresh_access_token", mock_refresh_token)
    mock_session = Mock(spec=httpx.Client)
    mock_session.post = Mock()

    def mock_client_init(self, *args, **kwargs):
        pass

    monkeypatch.setattr(httpx.Client, "__init__", mock_client_init)

    client = MostClient(
        client_id="test_client_id",
        client_secret="test_client_secret",
        etl_base_url="https://etl.test.ai",
    )
    client.session = mock_session
    client.access_token = "test_token"
    return client


def test_process_communication_by_id_success(mock_client):
    """Успешная отправка коммуникации в n8n."""
    mock_response = Mock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.json.return_value = {
        "success": True,
        "most_communication_id": "most-abc123",
        "execution_id": "exec-456",
        "error": None,
    }

    mock_client.session.post = Mock(return_value=mock_response)

    result = mock_client.process_communication_by_id("most-abc123")

    assert isinstance(result, ProcessCommunicationByIdResponse)
    assert result.success is True
    assert result.most_communication_id == "most-abc123"
    assert result.execution_id == "exec-456"
    assert result.error is None

    mock_client.session.post.assert_called_once()
    call_args = mock_client.session.post.call_args
    assert call_args[0][0] == (
        "https://etl.test.ai/api/v1/process_communication_by_id"
    )
    assert call_args[1]["headers"]["Authorization"] == "Bearer test_token"
    assert call_args[1]["json"] == {"most_communication_id": "most-abc123"}


def test_process_communication_by_id_success_with_kwargs(mock_client):
    """Успешная отправка с доп. полями через **kwargs (call_info)."""
    mock_response = Mock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.json.return_value = {
        "success": True,
        "most_communication_id": "most-xyz789",
        "execution_id": "exec-999",
        "error": None,
    }

    mock_client.session.post = Mock(return_value=mock_response)

    result = mock_client.process_communication_by_id(
        "most-xyz789",
        source_entity_id="ent-1",
        custom_flag=True,
    )

    assert result.success is True
    assert result.most_communication_id == "most-xyz789"

    call_args = mock_client.session.post.call_args
    body = call_args[1]["json"]
    assert body["most_communication_id"] == "most-xyz789"
    assert body["source_entity_id"] == "ent-1"
    assert body["custom_flag"] is True


def test_process_communication_by_id_n8n_non_200(mock_client):
    """Ответ 200 с success=False (n8n вернул не 200)."""
    mock_response = Mock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.json.return_value = {
        "success": False,
        "most_communication_id": "most-fail",
        "execution_id": None,
        "error": "n8n вернул статус 500",
    }

    mock_client.session.post = Mock(return_value=mock_response)

    result = mock_client.process_communication_by_id("most-fail")

    assert result.success is False
    assert result.error == "n8n вернул статус 500"


def test_process_communication_by_id_401_refresh_token(mock_client):
    """При 401 токен обновляется и запрос повторяется."""
    mock_response_401 = Mock(spec=httpx.Response)
    mock_response_401.status_code = 401
    mock_response_401.headers = {"Content-Type": "application/json"}

    mock_response_200 = Mock(spec=httpx.Response)
    mock_response_200.status_code = 200
    mock_response_200.headers = {"Content-Type": "application/json"}
    mock_response_200.json.return_value = {
        "success": True,
        "most_communication_id": "most-401",
        "execution_id": "exec-ok",
        "error": None,
    }

    mock_client.refresh_access_token = Mock()
    mock_client.access_token = "new_token"
    mock_client.session.post = Mock(
        side_effect=[mock_response_401, mock_response_200]
    )

    result = mock_client.process_communication_by_id("most-401")

    assert mock_client.refresh_access_token.called
    assert mock_client.session.post.call_count == 2
    assert result.success is True
    assert result.execution_id == "exec-ok"


def test_process_communication_by_id_403_raises(mock_client):
    """403 (коммуникация не принадлежит клиенту) приводит к RuntimeError."""
    mock_response = Mock(spec=httpx.Response)
    mock_response.status_code = 403
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.json.return_value = {
        "detail": "Коммуникация не принадлежит клиенту или недоступна в MOST",
    }

    mock_client.session.post = Mock(return_value=mock_response)

    with pytest.raises(RuntimeError, match="не принадлежит клиенту"):
        mock_client.process_communication_by_id("most-403")


def test_process_communication_by_id_503_raises(mock_client):
    """503 (Prefect/вебхук) приводит к RuntimeError."""
    mock_response = Mock(spec=httpx.Response)
    mock_response.status_code = 503
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.json.return_value = {
        "detail": "Не удалось получить креды или вебхук из Prefect: ...",
    }

    mock_client.session.post = Mock(return_value=mock_response)

    with pytest.raises(RuntimeError, match="Prefect"):
        mock_client.process_communication_by_id("most-503")
