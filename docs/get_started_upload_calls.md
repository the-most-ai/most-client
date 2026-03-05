# Get Started: загрузка коммуникаций на платформу Most AI

Краткое руководство по последовательной загрузке коммсуникаций и отправке их на оценку.

**Авторизационные данные** (client_id, client_secret) выдаст менеджер от нашей компании.  
**Дополнительные параметры** в `process_communication_by_id` нужно предварительно согласовать с технической командой.

---

## Установка SDK из PyPI (или воспользуйтесь API напрямую)

Можно работать через наш Python SDK или вызывать API напрямую (HTTP). Ниже для каждого шага приведены оба варианта.

**Через SDK:** установите пакет `most-client` через pip:

```bash
pip install most-client
```

После установки импортируйте клиент в коде:

```python
from most import MostClient
```

---

## Общая последовательность

1. **Загрузить звонок или текст** — `upload_audio` / `upload_audio_url` (аудио) или `upload_dialog` (текст диалога).
2. **Загрузить метаданные** — `upload_communications` (связь загруженного контента с вашими сущностями и датами).
3. **Отправить на оценку** — `process_communication_by_id` (запуск пайплайна оценки по ID коммуникации).

Во всех запросах используется один и тот же **Bearer-токен**, полученный по client_id и client_secret (см. ниже).

---

## 0. Получение токена доступа

Токен нужен для всех последующих запросов. SDK получает его сам при первом вызове.

### SDK

```python
from most import MostClient

client_id = "ВАШ_CLIENT_ID"       # от менеджера
client_secret = "ВАШ_CLIENT_SECRET"

client = MostClient(client_id=client_id, client_secret=client_secret)
# Токен запрашивается автоматически при первом post/get
```

### Сырой запрос к API

```http
POST https://api.the-most.ai/api/external/access_token
Content-Type: application/json

{
  "client_id": "ВАШ_CLIENT_ID",
  "client_secret": "ВАШ_CLIENT_SECRET"
}
```

Ответ — JSON с токеном (строка), например: `"eyJhbGc..."`.  
Это значение подставляется в заголовок: `Authorization: Bearer <токен>`.

---

## 1. Загрузка звонка или текста

Выполняется **один** из вариантов: аудиофайл, URL аудио или текст диалога. Если передаете URL, ресурс должен быть **без авторизации**.

### 1.1. upload_audio — загрузка аудиофайла

Загружает файл с диска на платформу.

#### SDK

```python
audio = client.upload_audio(audio_path="/path/to/call.mp3")
# audio.id — идентификатор загруженного аудио (most_communication_id для следующих шагов)
# audio.url — ссылка на файл на платформе
```

#### Сырой запрос к API

```http
POST https://api.the-most.ai/api/external/{client_id}/upload
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

audio_file: <бинарное содержимое файла>
```

Ответ (JSON):

```json
{
  "id": "most-xxxxxxxxxxxxxxxxxxxxxxxx",
  "url": "https://..."
}
```

`id` — это **most_communication_id**, он понадобится в шагах 2 и 3.

---

### 1.2. upload_audio_url — загрузка аудио по URL

Платформа сама скачивает аудио по переданной ссылке.

#### SDK

```python
audio = client.upload_audio_url(audio_url="https://your-cdn.com/call.mp3")
# audio.id — most_communication_id
```

#### Сырой запрос к API

```http
POST https://api.the-most.ai/api/external/{client_id}/upload_url
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "audio_url": "https://your-cdn.com/call.mp3"
}
```

Ответ — такой же как у `upload`: `{"id": "...", "url": "..."}`.

---

### 1.3. upload_dialog — загрузка текста диалога

Если грузите не аудио, а готовый текст диалога (реплики спикеров).

#### SDK

```python
from most.types import Dialog, DialogSegment

dialog = Dialog(segments=[
    DialogSegment(
      start_time_ms=0, 
      end_time_ms=1500,
      text="Здравствуйте", 
      speaker="Оператор"
      ),
    DialogSegment(
      start_time_ms=1500, 
      end_time_ms=4000, 
      text="Добрый день", 
      speaker="Клиент"
      ),
])
text_entity = client.upload_dialog(dialog)
# text_entity.id — most_communication_id для шагов 2 и 3
```

#### Сырой запрос к API

```http
POST https://api.the-most.ai/api/external/{client_id}/upload_dialog
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "dialog": {
    "segments": [
      {
        "start_time_ms": 0,
        "end_time_ms": 1500,
        "text": "Здравствуйте",
        "speaker": "Оператор"
      },
      {
        "start_time_ms": 1500,
        "end_time_ms": 4000,
        "text": "Добрый день",
        "speaker": "Клиент"
      }
    ]
  }
}
```

Ответ (JSON): `{"id": "most-xxxxxxxxxxxxxxxxxxxxxxxx"}`. Это **most_communication_id**.

---

## 2. upload_communications — загрузка метаданных

Связывает загруженный звонок/текст (most_communication_id) с вашими сущностями: дата/время, менеджер, длительность и т.д.

#### SDK

```python
from most.types import CommunicationRequest

communications = [
    CommunicationRequest(
        source_entity_id="ваш_внутренний_id_звонка",
        most_communication_id=audio.id,  # id из шага 1
        start_dt="2025-03-05T10:00:00",
        manager="ivanov",
        end_dt="2025-03-05T10:05:00",
        talk_duration=300,
        client_phone="+79001234567",
        communication_type="call",
    )
]
result = client.upload_communications(communications, overwrite=False)
# result.status_per_communication, result.total_saved, result.success
```

#### Сырой запрос к API

Эндпоинт метаданных находится на **ETL** (другой хост):

```http
POST https://etl.the-most.ai/api/v1/communications
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "communications": [
    {
      "source_entity_id": "ваш_внутренний_id_звонка",
      "most_communication_id": "most-xxxxxxxxxxxxxxxxxxxxxxxx",
      "start_dt": "2025-03-05T10:00:00",
      "manager": "ivanov",
      "end_dt": "2025-03-05T10:05:00",
      "talk_duration": 300,
      "client_phone": "+79001234567",
      "communication_type": "call"
    }
  ],
  "overwrite": false
}
```

Минимально обязательные поля в каждом элементе: `source_entity_id`, `most_communication_id`, `start_dt`, `manager`. Остальные — опционально (см. `CommunicationRequest` в коде/типах).

---

## 3. process_communication_by_id — отправка на оценку

Запускает обработку и оценку коммуникации по её ID на платформе.  
**Дополнительные параметры** (все, что кроме `most_communication_id`) нужно заранее согласовать с технической командой.

#### SDK

```python
resp = client.process_communication_by_id(
    most_communication_id=audio.id,
    # Далее — любые доп. параметры, согласованные с тех. командой, например:
    # campaign_id="spring_2025",
    # channel="phone",
)
# resp.success, resp.most_communication_id, resp.execution_id, resp.error
```

#### Сырой запрос к API

Тот же ETL-хост:

```http
POST https://etl.the-most.ai/api/v1/process_communication_by_id
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "most_communication_id": "most-xxxxxxxxxxxxxxxxxxxxxxxx"
}
```

Если договорились о доп. полях — добавляете их в тот же JSON, например:

```json
{
  "most_communication_id": "most-xxxxxxxxxxxxxxxxxxxxxxxx",
  "campaign_id": "spring_2025",
  "channel": "phone"
}
```

Ответ (JSON):

```json
{
  "success": true,
  "most_communication_id": "most-xxxxxxxxxxxxxxxxxxxxxxxx",
  "execution_id": "...",
  "error": null
}
```

---

## Сводка URL и методов

| Шаг | Метод SDK | Хост | Метод HTTP | Путь |
|-----|-----------|------|------------|------|
| Токен | (внутри MostClient) | api.the-most.ai | POST | /api/external/access_token |
| Аудио файл | upload_audio | api.the-most.ai | POST | /api/external/{client_id}/upload |
| Аудио URL | upload_audio_url | api.the-most.ai | POST | /api/external/{client_id}/upload_url |
| Текст диалога | upload_dialog | api.the-most.ai | POST | /api/external/{client_id}/upload_dialog |
| Метаданные | upload_communications | etl.the-most.ai | POST | /api/v1/communications |
| Запуск оценки | process_communication_by_id | etl.the-most.ai | POST | /api/v1/process_communication_by_id |

Во всех запросах (кроме получения токена): заголовок `Authorization: Bearer <access_token>`.
