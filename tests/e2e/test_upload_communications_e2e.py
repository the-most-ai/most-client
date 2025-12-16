import os
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path

import httpx
import pytest

from most.api import MostClient
from most.types import CommunicationRequest


# Значения по умолчанию используются только если переменные окружения не установлены
# Для production используйте переменные окружения MOST_CLIENT_ID и MOST_CLIENT_SECRET
DEFAULT_ETL_BASE_URL = "https://etl.the-most.ai"
os.environ["MOST_CLIENT_ID"] = "67239029570a08554fc1f5a6"
os.environ["MOST_CLIENT_SECRET"] = "iXGO0XpvjRFC6H1vrXVOqQ$U0bGDpEUt09pOeIzVmS0G1v1dOrjNeC.1V3iDlKhfZc"


def handle_etl_registration_error(func):
    """Вспомогательная функция для обработки ошибки регистрации клиента в ETL"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except RuntimeError as e:
            error_msg = str(e)
            if "не зарегистрирован" in error_msg or "not registered" in error_msg.lower():
                pytest.skip(f"Клиент не зарегистрирован в ETL системе. Обратитесь к команде Most AI для регистрации: {error_msg}")
            raise
    return wrapper 


@pytest.fixture()
def most_client_etl(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> MostClient:
    """Фикстура для клиента с поддержкой ETL API
    
    Требует установки переменных окружения:
    - MOST_CLIENT_ID: ID клиента в MOST
    - MOST_CLIENT_SECRET: Секрет клиента в MOST
    - MOST_ETL_BASE_URL: (опционально) Базовый URL для ETL API, по умолчанию https://etl.the-most.ai
    - MOST_BASE_URL: (опционально) Базовый URL для основного API
    """
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))

    # Читаем переменные окружения (могут быть установлены через os.environ или системные переменные)
    client_id = os.environ.get("MOST_CLIENT_ID")
    client_secret = os.environ.get("MOST_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        pytest.skip(
            "Требуются переменные окружения MOST_CLIENT_ID и MOST_CLIENT_SECRET. "
            "Установите их перед запуском тестов."
        )
    
    base_url = os.environ.get("MOST_BASE_URL")
    etl_base_url = os.environ.get("MOST_ETL_BASE_URL") or DEFAULT_ETL_BASE_URL
    model_id = os.environ.get("MOST_MODEL_ID")

    try:
        client = MostClient(
            client_id=client_id,
            client_secret=client_secret,
            base_url=base_url,
            etl_base_url=etl_base_url,
            model_id=model_id,
        )
    except httpx.HTTPError as exc:
        pytest.fail(f"MOST API unavailable: {exc}")

    try:
        yield client
    finally:
        client.session.close()


@handle_etl_registration_error
def test_upload_communications_with_objects(most_client_etl):
    """Тест загрузки коммуникаций с объектами CommunicationRequest"""
    communications = [
        CommunicationRequest(
            source_entity_id=f"test_{datetime.now(timezone.utc).timestamp()}",
            most_communication_id=f"most-test-{datetime.now(timezone.utc).timestamp()}",
            start_dt=datetime.now(timezone.utc).isoformat(),
            end_dt=datetime.now(timezone.utc).isoformat(),
            manager="Тестовый Менеджер",
            talk_duration=300,
            communication_type="call",
            communication_direction="inbound",
            communication_result="answered",
        )
    ]

    result = most_client_etl.upload_communications(communications)

    assert result is not None
    assert result.total_saved >= 0
    assert len(result.status_per_communication) > 0


@handle_etl_registration_error
def test_upload_communications_with_dicts(most_client_etl):
    """Тест загрузки коммуникаций со словарями"""
    now = datetime.now(timezone.utc)
    communications = [
        {
            "source_entity_id": f"test_dict_{now.timestamp()}",
            "most_communication_id": f"most-dict-{now.timestamp()}",
            "start_dt": now.isoformat(),
            "end_dt": now.isoformat(),
            "manager": "Тестовый Менеджер 2",
            "talk_duration": 180,
            "communication_type": "chat",
            "communication_direction": "outbound",
            "status": "completed",
        }
    ]

    result = most_client_etl.upload_communications(communications)

    assert result is not None
    assert result.total_saved >= 0
    assert len(result.status_per_communication) > 0


@handle_etl_registration_error
def test_upload_communications_with_optional_fields(most_client_etl):
    """Тест загрузки коммуникаций с опциональными полями"""
    now = datetime.now(timezone.utc)
    communications = [
        CommunicationRequest(
            source_entity_id=f"test_optional_{now.timestamp()}",
            most_communication_id=f"most-optional-{now.timestamp()}",
            start_dt=now.isoformat(),
            end_dt=now.isoformat(),
            manager="Тестовый Менеджер 3",
            talk_duration=250,
            client_phone="+79991234567",
            wait_duration=30,
            status="completed",
            communication_result="answered",
            communication_type="call",
            communication_direction="inbound",
            extra_fields={"custom_field": "test_value", "another_field": 123},
            tech_fields={"tech_field": "tech_value"},
        )
    ]

    result = most_client_etl.upload_communications(communications)

    assert result is not None
    assert result.total_saved >= 0
    assert len(result.status_per_communication) > 0


@handle_etl_registration_error
def test_upload_communications_batch(most_client_etl):
    """Тест загрузки нескольких коммуникаций пачкой"""
    now = datetime.now(timezone.utc)
    communications = [
        CommunicationRequest(
            source_entity_id=f"test_batch_{i}_{now.timestamp()}",
            most_communication_id=f"most-batch-{i}-{now.timestamp()}",
            start_dt=now.isoformat(),
            end_dt=now.isoformat(),
            manager=f"Менеджер {i}",
            talk_duration=100 + i * 10,
            communication_type="call",
        )
        for i in range(3)
    ]

    result = most_client_etl.upload_communications(communications)

    assert result is not None
    assert result.total_saved >= 0
    assert len(result.status_per_communication) == 3


@handle_etl_registration_error
def test_upload_communications_with_overwrite(most_client_etl):
    """Тест загрузки с параметром overwrite=True"""
    now = datetime.now(timezone.utc)
    source_id = f"test_overwrite_{now.timestamp()}"
    
    communications = [
        CommunicationRequest(
            source_entity_id=source_id,
            most_communication_id=f"most-overwrite-{now.timestamp()}",
            start_dt=now.isoformat(),
            end_dt=now.isoformat(),
            manager="Тестовый Менеджер Overwrite",
            talk_duration=200,
            communication_type="call",
        )
    ]

    # Первая загрузка
    result1 = most_client_etl.upload_communications(communications, overwrite=False)
    assert result1 is not None

    # Вторая загрузка с overwrite=True
    result2 = most_client_etl.upload_communications(communications, overwrite=True)
    assert result2 is not None
    assert result2.total_saved >= 0


@handle_etl_registration_error
def test_upload_communications_empty_list(most_client_etl):
    """Тест загрузки пустого списка коммуникаций - должен вернуть ошибку валидации"""
    communications = []

    # API не принимает пустой список, должна быть ошибка валидации
    with pytest.raises(RuntimeError, match="Validation error.*пуст|пуст.*Validation error"):
        most_client_etl.upload_communications(communications)


@handle_etl_registration_error
def test_upload_communications_mixed_types(most_client_etl):
    """Тест загрузки коммуникаций со смешанными типами (объекты и словари)"""
    now = datetime.now(timezone.utc)
    communications = [
        CommunicationRequest(
            source_entity_id=f"test_mixed_obj_{now.timestamp()}",
            most_communication_id=f"most-mixed-obj-{now.timestamp()}",
            start_dt=now.isoformat(),
            end_dt=now.isoformat(),
            manager="Менеджер Объект",
            talk_duration=150,
        ),
        {
            "source_entity_id": f"test_mixed_dict_{now.timestamp()}",
            "most_communication_id": f"most-mixed-dict-{now.timestamp()}",
            "start_dt": now.isoformat(),
            "end_dt": now.isoformat(),
            "manager": "Менеджер Словарь",
            "talk_duration": 200,
        },
    ]

    result = most_client_etl.upload_communications(communications)

    assert result is not None
    assert result.total_saved >= 0
    assert len(result.status_per_communication) == 2

