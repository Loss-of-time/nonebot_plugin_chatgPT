__author__ = "loss0fTime"

from pydantic import BaseModel

class Config(BaseModel):
    chatgpt_api_key: str
    """The api key of chatgpt"""

    chatgpt_bot_id: int = 0
    """The qq id of bot"""

    chatgpt_max_tokens: int = 300

    chatgpt_api_url: str = "https://api.openai.com/v1/"

    chatgpt_max_message_num: int = 8

    chatgpt_model: str = "gpt-4o"

    chatgpt_prompt: str = ""
    """The prompt of chatgpt"""

    chatgpt_enable_random_reply: bool = False
    """Whether to enable random reply"""

    chatgpt_random_reply_whitelist: list[int] = []

    chatgpt_random_reply_percentage: int = 20
