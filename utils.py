# utils.py

import base64
import aiohttp
from io import BytesIO
from PIL import Image
from typing import List, TYPE_CHECKING

from .models import Model

if TYPE_CHECKING:
    from loguru import Logger


async def url_to_base64(
    url: str, max_size_kb: int = 512, max_dimension: int = 1024
) -> str:
    url = url.replace("https://", "http://") if url.startswith("https://") else url
    async with aiohttp.ClientSession() as session:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }
        async with session.get(url, headers=headers) as response:
            image_data = await response.read()

    # compressed_image_data = compress_image(image_data, max_size_kb, max_dimension)
    return base64.b64encode(image_data).decode("utf-8")


def compress_image(image_data: bytes, max_size_kb: int, max_dimension: int) -> bytes:
    image = Image.open(BytesIO(image_data))

    if image.mode != "RGBA":
        image = image.convert("RGB")

    if max(image.size) > max_dimension:
        image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

    buffer = BytesIO()
    quality = 100

    while True:
        buffer.seek(0)
        buffer.truncate()
        size_kb = buffer.tell() / 1024

        if size_kb <= max_size_kb or quality <= 5:
            break
        image.save(buffer, format="JPEG", quality=quality)

        quality -= 5

    return buffer.getvalue()


async def call_api(
    model: Model,
    messages: List[dict],
    api_key: str,
    api_url: str,
    max_tokens: int,
    logger: "Logger",
) -> tuple[int, str]:
    async with aiohttp.ClientSession() as session:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        data = {
            "model": model.value,
            "messages": messages,
            "max_tokens": max_tokens,
        }
        try:
            async with session.post(
                f"{api_url}/chat/completions", json=data, headers=headers
            ) as resp:
                try:
                    response = await resp.json()
                    return 0, response["choices"][0]["message"]["content"]
                except:
                    return 1, f"API调用失败：{resp.status}"
        except Exception as e:
            return 1, f"API调用失败：{e}"
