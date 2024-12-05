import argparse
import asyncio
from pathlib import Path

from most.async_api import AsyncMostClient


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("audio_path",
                        type=Path)
    args = parser.parse_args()
    return args


async def main(audio_path: Path):
    async with AsyncMostClient() as client:
        models = await client.list_models()
        print(models)

        model = models[0]

        script = await model.get_model_script()
        print(script)

        audios = await client.list_audios()
        print(audios)

        audio = await client.upload_audio(audio_path)
        print(audio)

        result = await model.apply(audio.id)
        print(result)


if __name__ == '__main__':
    asyncio.run(main(**vars(parse_args())))
