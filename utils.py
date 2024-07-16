import base64
import aiohttp
from enum import Enum
from typing import List, Dict
from typing import TYPE_CHECKING

from io import BytesIO
from PIL import Image

if TYPE_CHECKING:
    from loguru import Logger


class Role(Enum):
    ASSISTANT = "assistant"
    USER = "user"
    SYSTEM = "system"


class Model(Enum):
    GPT_4O = "gpt-4o"
    CLAUDE = "claude-3-5-sonnet-20240620"
    GPT_4_ALL = "gpt-4-all"


async def url_to_base64(url: str, max_size_kb: int = 512, max_dimension: int = 1024) -> str:
    # Replace https with http for the given URL
    if url.split("://")[0] == "https":
        url = url.replace("https://", "http://")

    # Create an async session
    async with aiohttp.ClientSession() as session:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }
        # Fetch the image data
        async with session.get(url, headers=headers) as response:
            image_data = await response.read()

    # Compress the image
    compressed_image_data = compress_image(image_data, max_size_kb, max_dimension)
    
    # Encode the compressed image data to Base64
    return base64.b64encode(compressed_image_data).decode("utf-8")

def compress_image(image_data: bytes, max_size_kb: int, max_dimension: int) -> bytes:
    # Load the image data into a PIL image
    image = Image.open(BytesIO(image_data))
    
    # Convert image to RGB if it has an alpha channel
    if image.mode == 'RGBA':
        image = image.convert('RGB')

    # Resize the image if necessary
    if max(image.size) > max_dimension:
        image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

    # Initialize variables for compression
    buffer = BytesIO()
    quality = 95

    # Compress the image iteratively until it's smaller than the max_size_kb
    while True:
        buffer.seek(0)
        buffer.truncate()
        image.save(buffer, format="JPEG", quality=quality)
        size_kb = buffer.tell() / 1024  # Size in KB

        if size_kb <= max_size_kb or quality <= 5:
            break
        
        quality -= 5  # Decrease quality for higher compression

    # Get the compressed image data
    return buffer.getvalue()

async def basic_call_api(
    model: Model, messages: List[dict], api_key: str, api_url: str, max_tokens: int, logger: "Logger"
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
                # logger.debug(f"API response: {await resp.text()}")
                try:
                    response = await resp.json()
                    return 0, response["choices"][0]["message"]["content"]
                except:
                    return 1, f"API调用失败：{resp.status} {await resp.text()}"
        except Exception as e:
            return 1, f"API调用失败：{e}"