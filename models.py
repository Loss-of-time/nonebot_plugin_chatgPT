# models.py

from enum import Enum
from typing import List, Dict

class Role(Enum):
    ASSISTANT = "assistant"
    USER = "user"
    SYSTEM = "system"

class Model(Enum):
    GPT_4O = "gpt-4o"
    CLAUDE = "claude-3-5-sonnet-20240620"
    GPT_4_ALL = "gpt-4-all"

class GroupMessageHistory:
    def __init__(self, max_message_num: int):
        self.max_message_num = max_message_num
        self.messages: List[dict] = []

    def append_message(self, message: dict) -> None:
        if len(self.messages) >= self.max_message_num:
            self.messages.pop(0)
        self.messages.append(message)

    def get_messages(self) -> List[dict]:
        return self.messages

    def get_merged_messages(self) -> List[dict]:
        merged_messages = []
        for message in self.messages:
            if message["role"] == Role.USER.value:
                self.combine_user_messages(merged_messages, message["content"])
            else:
                merged_messages.append(message)
        return merged_messages

    def clear(self) -> None:
        self.messages = []

    @staticmethod
    def combine_user_messages(messages: List[dict], new_content: List[dict]) -> None:
        if messages and messages[-1]["role"] == Role.USER.value:
            messages[-1]["content"].extend(new_content)
        else:
            messages.append({"role": Role.USER.value, "content": new_content})

        if messages[-1]["role"] != Role.USER.value:
            messages.append({"role": Role.USER.value, "content": []})

    def __str__(self) -> str:
        result = ""
        for message in self.messages:
            for segment in message["content"]:
                if segment["type"] == "text":
                    text = segment["text"]
                    if len(text) > 20:
                        text = text[:20] + "..."
                    result += text
                elif segment["type"] == "image_url":
                    result += "[图片]"
            result += "\n"
        return result

groups_message: Dict[int, GroupMessageHistory] = {}
id_to_card: dict[str, str] = {}