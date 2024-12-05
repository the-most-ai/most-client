import argparse
from pathlib import Path

from most.api import MostClient


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("audio_path",
                        type=Path)
    args = parser.parse_args()
    return args


def main(audio_path: Path):
    client = MostClient()

    models = client.list_models()
    print(models)

    model = models[0]

    script = model.get_model_script()
    print(script)

    audios = client.list_audios()
    print(audios)

    audio = client.upload_audio(audio_path)
    print(audio)

    result = model.apply(audio.id)
    print(result)


if __name__ == '__main__':
    main(**vars(parse_args()))
