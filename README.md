# MOST AI Python Client  


```python
from most import MostClient

most = MostClient(model_id="most-***")

audio_path = "example.mp3"
results = most(audio_path)
print(results)

{
    "id": "AudioID",
    "url": "Audio CDN Url",
    "text": "Transcribed text from audio",
    "results": [
        {
            "name": "Приветствие",
            "subcolumns": [
                {
                    "name": "Назвал свое имя",
                    "description": "Менеджер назвал свое имя - Алина",
                    "score": 2,
                }
            ]
        }
    ]
}

most.store_info(results['id'], {
    "key1": "value1"
})

most.fetch_info(results['id'])
```
