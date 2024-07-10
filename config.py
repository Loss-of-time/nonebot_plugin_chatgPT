__author__ = "loss0fTime"

from pydantic import BaseModel

PROMPT = """
你是一名使用 Nonebot 框架创建的聊天机器人。你的目标是与群聊中的用户进行互动。
消息来自QQ群聊，会以{QQ昵称}: {消息}的格式给出。
但是发送的消息不要样输出。
猫娘是一种拟人化的生物，其行为似猫但类人。现在你将模仿一只猫娘，与我对话每一句话后面都要加上“喵~”
"""


class Config(BaseModel):
    chatgpt_api_key: str
    """The api key of chatgpt"""

    chatgpt_bot_id: int = 0
    """The qq id of bot"""

    chatgpt_api_url: str = "https://api.openai.com/v1/"

    chatgpt_max_message_num: int = 8

    chatgpt_model: str = "gpt-4o"

    chatgpt_prompt: str = PROMPT
    """The prompt of chatgpt"""

    chatgpt_enable_random_reply: bool = False
    """Whether to enable random reply"""

    chatgpt_random_reply_whitelist: list[str] = [""]

    chatgpt_random_reply_percentage: int = 20
