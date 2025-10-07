import time
import wave
from pathlib import Path

import httpx

from most.types import Result, Text


def _write_silence_wav(path: Path, duration_seconds: float = 0.1, sample_rate: int = 16000) -> None:
    frames = int(duration_seconds * sample_rate)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(b"\x00\x00" * frames)


def _wait_for_text(
    most_client,
    data_id: str,
    data_source: str = "audio",
    attempts: int = 30,
    delay_seconds: float = 1.0,
) -> Result:
    last_error: Exception | None = None
    result: Result | None = None
    for _ in range(attempts):
        try:
            result = most_client.fetch_text(data_id, data_source=data_source)
        except (RuntimeError, httpx.HTTPError) as exc:
            last_error = exc
            time.sleep(delay_seconds)
            continue
        if getattr(result, "text", None):
            return result
        time.sleep(delay_seconds)
    if last_error is not None:
        raise last_error
    assert result is not None
    return result


def test_upload_text_and_audio_roundtrip(most_client, tmp_path: Path) -> None:
    text: Text = most_client.upload_text("Hello, MOST!")
    assert text.id

    fetched_text = _wait_for_text(most_client, text.id, data_source="text")
    assert fetched_text.id
    assert getattr(fetched_text, "text", None)

    audio_file = tmp_path / "sample.wav"
    _write_silence_wav(audio_file)

    audio = most_client.upload_audio(audio_file)
    assert audio.id
    assert audio.url

    fetched_audio_text = _wait_for_text(most_client, audio.id, data_source="audio")
    assert fetched_audio_text.id
    assert getattr(fetched_audio_text, "text", None)
