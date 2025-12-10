from unittest.mock import Mock, patch
import pytest
import httpx

from most.api import MostClient
from most.types import (
    CommunicationRequest,
    CommunicationBatchResponse,
    CommunicationResponse,
)


@pytest.fixture
def mock_client(monkeypatch):
    """Создает клиент с мокированным HTTP сессией"""
    # Мокируем refresh_access_token чтобы не делать реальный запрос при инициализации
    def mock_refresh_token(self):
        self.access_token = "test_token"
    
    # Мокируем до создания клиента
    monkeypatch.setattr(MostClient, "refresh_access_token", mock_refresh_token)
    
    # Создаем мокированную сессию с мокированным post
    mock_session = Mock(spec=httpx.Client)
    mock_session.post = Mock()
    
    # Мокируем httpx.Client чтобы вернуть нашу мокированную сессию
    original_client_init = httpx.Client.__init__
    
    def mock_client_init(self, *args, **kwargs):
        # Не делаем ничего, просто пропускаем инициализацию
        pass
    
    monkeypatch.setattr(httpx.Client, "__init__", mock_client_init)
    
    client = MostClient(
        client_id="test_client_id",
        client_secret="test_client_secret",
        etl_base_url="https://etl.test.ai"
    )
    
    # Заменяем сессию на мок после создания
    client.session = mock_session
    client.access_token = "test_token"
    
    return client


def test_upload_communications_with_objects_success(mock_client):
    """Тест успешной загрузки коммуникаций с объектами CommunicationRequest"""
    communications = [
        CommunicationRequest(
            source_entity_id="123",
            most_communication_id="most-abc123",
            start_dt="2024-01-01T10:00:00Z",
            end_dt="2024-01-01T10:05:00Z",
            manager="Иван Иванов",
            talk_duration=300,
            communication_type="call",
            communication_direction="inbound"
        )
    ]

    mock_response = Mock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.json.return_value = {
        "success": True,
        "status_per_communication": {
            "123": {
                "success": True,
                "reason": "saved"
            }
        },
        "total_saved": 1
    }

    mock_client.session.post = Mock(return_value=mock_response)

    result = mock_client.upload_communications(communications)

    assert isinstance(result, CommunicationBatchResponse)
    assert result.success is True
    assert result.total_saved == 1
    assert "123" in result.status_per_communication
    assert result.status_per_communication["123"].success is True
    assert result.status_per_communication["123"].reason == "saved"

    # Проверяем, что был вызван правильный URL
    mock_client.session.post.assert_called_once()
    call_args = mock_client.session.post.call_args
    assert call_args[0][0] == "https://etl.test.ai/api/v1/communications"
    assert call_args[1]["headers"]["Authorization"] == "Bearer test_token"


def test_upload_communications_with_dicts_success(mock_client):
    """Тест успешной загрузки коммуникаций со словарями"""
    communications = [
        {
            "source_entity_id": "456",
            "most_communication_id": "most-def456",
            "start_dt": "2024-01-01T11:00:00Z",
            "end_dt": "2024-01-01T11:05:00Z",
            "manager": "Петр Петров",
            "talk_duration": 180,
            "communication_type": "chat",
            "communication_direction": "outbound"
        }
    ]

    mock_response = Mock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.json.return_value = {
        "success": True,
        "status_per_communication": {
            "456": {
                "success": True,
                "reason": "saved"
            }
        },
        "total_saved": 1
    }

    mock_client.session.post = Mock(return_value=mock_response)

    result = mock_client.upload_communications(communications)

    assert isinstance(result, CommunicationBatchResponse)
    assert result.total_saved == 1
    assert "456" in result.status_per_communication


def test_upload_communications_with_mixed_types(mock_client):
    """Тест загрузки коммуникаций со смешанными типами (объекты и словари)"""
    communications = [
        CommunicationRequest(
            source_entity_id="789",
            most_communication_id="most-ghi789",
            start_dt="2024-01-01T12:00:00Z",
            end_dt="2024-01-01T12:05:00Z",
            manager="Сидор Сидоров",
            talk_duration=240
        ),
        {
            "source_entity_id": "101",
            "most_communication_id": "most-jkl101",
            "start_dt": "2024-01-01T13:00:00Z",
            "end_dt": "2024-01-01T13:05:00Z",
            "manager": "Василий Васильев",
            "talk_duration": 120
        }
    ]

    mock_response = Mock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.json.return_value = {
        "success": True,
        "status_per_communication": {
            "789": {"success": True, "reason": "saved"},
            "101": {"success": True, "reason": "saved"}
        },
        "total_saved": 2
    }

    mock_client.session.post = Mock(return_value=mock_response)

    result = mock_client.upload_communications(communications)

    assert result.total_saved == 2
    assert len(result.status_per_communication) == 2


def test_upload_communications_with_overwrite(mock_client):
    """Тест загрузки с параметром overwrite=True"""
    communications = [
        CommunicationRequest(
            source_entity_id="999",
            most_communication_id="most-xyz999",
            start_dt="2024-01-01T14:00:00Z",
            end_dt="2024-01-01T14:05:00Z",
            manager="Тест Тестов",
            talk_duration=100
        )
    ]

    mock_response = Mock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.json.return_value = {
        "success": True,
        "status_per_communication": {
            "999": {"success": True, "reason": "overwritten"}
        },
        "total_saved": 1
    }

    mock_client.session.post = Mock(return_value=mock_response)

    result = mock_client.upload_communications(communications, overwrite=True)

    # Проверяем, что overwrite был передан в запросе
    call_args = mock_client.session.post.call_args
    request_data = call_args[1]["json"]
    assert request_data["overwrite"] is True


def test_upload_communications_invalid_type_error(mock_client):
    """Тест ошибки при передаче невалидного типа"""
    communications = ["invalid_type", 123, None]

    with pytest.raises(TypeError, match="Ожидается CommunicationRequest или dict"):
        mock_client.upload_communications(communications)


def test_upload_communications_401_refresh_token(mock_client):
    """Тест обновления токена при 401 ошибке"""
    communications = [
        CommunicationRequest(
            source_entity_id="401_test",
            most_communication_id="most-401",
            start_dt="2024-01-01T15:00:00Z",
            end_dt="2024-01-01T15:05:00Z",
            manager="Тест 401",
            talk_duration=200
        )
    ]

    # Первый запрос возвращает 401
    mock_response_401 = Mock(spec=httpx.Response)
    mock_response_401.status_code = 401
    mock_response_401.headers = {"Content-Type": "application/json"}

    # Второй запрос после обновления токена успешен
    mock_response_200 = Mock(spec=httpx.Response)
    mock_response_200.status_code = 200
    mock_response_200.headers = {"Content-Type": "application/json"}
    mock_response_200.json.return_value = {
        "success": True,
        "status_per_communication": {
            "401_test": {"success": True, "reason": "saved"}
        },
        "total_saved": 1
    }

    # Мокируем refresh_access_token
    mock_client.refresh_access_token = Mock()
    mock_client.access_token = "new_token"

    # Мокируем post чтобы вернуть разные ответы
    mock_client.session.post = Mock(side_effect=[mock_response_401, mock_response_200])

    result = mock_client.upload_communications(communications)

    # Проверяем, что токен был обновлен
    assert mock_client.refresh_access_token.called
    # Проверяем, что было два вызова (первый 401, второй успешный)
    assert mock_client.session.post.call_count == 2
    assert result.total_saved == 1


def test_upload_communications_validation_error(mock_client):
    """Тест обработки ошибки валидации на уровне клиента (неполные данные)"""
    communications = [
        {
            "source_entity_id": "invalid",
            # Неполные данные - нет обязательных полей
        }
    ]

    # Валидация происходит на уровне retort.load() до отправки запроса
    # adaptix выбрасывает ExceptionGroup или другие исключения при ошибках валидации
    with pytest.raises(Exception):  # Может быть ExceptionGroup, ValueError, TypeError и т.д.
        mock_client.upload_communications(communications)


def test_upload_communications_generic_error(mock_client):
    """Тест обработки общей ошибки (400+)"""
    communications = [
        CommunicationRequest(
            source_entity_id="error_test",
            most_communication_id="most-error",
            start_dt="2024-01-01T16:00:00Z",
            end_dt="2024-01-01T16:05:00Z",
            manager="Тест Ошибка",
            talk_duration=150
        )
    ]

    mock_response = Mock(spec=httpx.Response)
    mock_response.status_code = 500
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.json.return_value = {
        "message": "Internal server error"
    }

    mock_client.session.post = Mock(return_value=mock_response)

    with pytest.raises(RuntimeError, match="Internal server error"):
        mock_client.upload_communications(communications)


def test_upload_communications_empty_list(mock_client):
    """Тест загрузки пустого списка коммуникаций"""
    communications = []

    mock_response = Mock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.json.return_value = {
        "success": True,
        "status_per_communication": {},
        "total_saved": 0
    }

    mock_client.session.post = Mock(return_value=mock_response)

    result = mock_client.upload_communications(communications)

    assert result.total_saved == 0
    assert len(result.status_per_communication) == 0


def test_upload_communications_with_optional_fields(mock_client):
    """Тест загрузки с опциональными полями"""
    communications = [
        CommunicationRequest(
            source_entity_id="optional_test",
            most_communication_id="most-optional",
            start_dt="2024-01-01T17:00:00Z",
            end_dt="2024-01-01T17:05:00Z",
            manager="Тест Опциональный",
            talk_duration=250,
            client_phone="+79991234567",
            wait_duration=30,
            status="completed",
            communication_result="answered",
            extra_fields={"custom_field": "value"},
            tech_fields={"tech_field": 123}
        )
    ]

    mock_response = Mock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.json.return_value = {
        "status_per_communication": {
            "optional_test": {"reason": "saved", "success": True}
        },
        "total_saved": 1,
        "success": True
    }

    mock_client.session.post = Mock(return_value=mock_response)

    result = mock_client.upload_communications(communications)

    assert result.total_saved == 1
    # Проверяем, что опциональные поля были переданы
    call_args = mock_client.session.post.call_args
    request_data = call_args[1]["json"]
    comm_data = request_data["communications"][0]
    assert comm_data["client_phone"] == "+79991234567"
    assert comm_data["wait_duration"] == 30
    assert comm_data["extra_fields"] == {"custom_field": "value"}

