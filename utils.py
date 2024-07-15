import base64
import aiohttp
from enum import Enum
from typing import List, Dict
from typing import TYPE_CHECKING

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


async def url_to_base64(url: str) -> str:
    if url.split("://")[0] == "https":
        url = url.replace("https://", "http://")
    async with aiohttp.ClientSession() as session:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }
        async with session.get(url, headers=headers) as response:
            image_data = await response.read()
            return base64.b64encode(image_data).decode("utf-8")


async def basic_call_api(
    model: Model, messages: List[dict], api_key: str, api_url: str, max_tokens: int,logger: "Logger"
) -> str:
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
        async with session.post(
            f"{api_url}/chat/completions", json=data, headers=headers, timeout=120
        ) as resp:
            # logger.debug(f"API response: {await resp.text()}")
            try:
                response = await resp.json()
                return response["choices"][0]["message"]["content"]
            except:
                return f"API调用失败：{resp.status} {await resp.text()}"