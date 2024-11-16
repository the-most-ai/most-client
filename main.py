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
    client.refresh_access_token()
    print(client.list_models())
    audio_id = client.upload_audio(audio_path)
    print("Audio ID: {}".format(audio_id))


if __name__ == '__main__':
    main(**vars(parse_args()))
