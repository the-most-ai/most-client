from pydub import AudioSegment
from pathlib import Path
from most.types import Text


def _write_silence_wav(path: Path, duration_seconds: float = 0.1, sample_rate: int = 16000) -> None:
    audio = AudioSegment.silent(duration=duration_seconds)
    audio.export(path, format="wav")


def test_upload_text_and_audio_roundtrip(most_client, tmp_path: Path) -> None:
    text: Text = most_client.upload_text("Hello, MOST!")
    assert text.id

    fetched_text = most_client.fetch_text(text.id,
                                          data_source="text")
    assert fetched_text.id
    assert fetched_text.id == text.id
    assert fetched_text.text == "Hello, MOST!"

    audio_file = tmp_path / "sample.wav"
    _write_silence_wav(audio_file)

    audio = most_client.upload_audio(audio_file)
    assert audio.id
    assert audio.url

    text_obj = most_client.upload_text("Привет, мир!")
    assert text_obj.id

    # if most_client.model_id:
    #     result = most_client.apply_on_text(text_obj.id,
    #                                        overwrite=True)
    #     assert result.id
    #     assert result.results
