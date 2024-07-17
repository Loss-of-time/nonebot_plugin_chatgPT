# config.py

from pydantic import BaseModel, Field
from typing import List

class Config(BaseModel):
    chatgpt_api_key: str = Field(..., description="The API key for ChatGPT")
    chatgpt_bot_id: int = Field(0, description="The QQ ID of the bot")
    chatgpt_max_tokens: int = Field(300, description="Maximum number of tokens for API response")
    chatgpt_api_url: str = Field("https://api.openai.com/v1/", description="ChatGPT API URL")
    chatgpt_max_message_num: int = Field(8, description="Maximum number of messages to keep in history")
    chatgpt_model: str = Field("gpt-4o", description="ChatGPT model to use")
    chatgpt_prompt: str = Field("", description="Default prompt for ChatGPT")
    chatgpt_enable_random_reply: bool = Field(False, description="Enable random replies")
    chatgpt_random_reply_whitelist: List[int] = Field(default_factory=list, description="Whitelist for random replies")
    chatgpt_random_reply_percentage: int = Field(20, description="Percentage chance of random reply")