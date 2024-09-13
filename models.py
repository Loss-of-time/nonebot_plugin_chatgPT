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
    # A message structure example (OpenAI format):
    # {
    #     "role": "user" or "assistant" or "system",
    #     "content": [
    #         {
    #             "type": "text",
    #             "text": "some text content"
    #         },
    #         {
    #             "type": "image_url",
    #             "url": "http://example.com/image.png"
    #         }
    #     ]
    # }
    def __init__(self, max_message_num: int):
        self.max_message_num = max_message_num
        self.messages: List[dict] = []

    def append_message(self, message: dict) -> None:
        if len(self.messages) >= self.max_message_num:
            self.messages.pop(0)
            while self.messages and self.messages[0]["role"] == Role.USER.value:
                self.messages.pop(0)
        self.messages.append(message)

    def get_messages(self) -> List[dict]:
        return self.messages

    def get_merged_messages(self) -> List[dict]:
        merged_messages = []
        for message in self.messages:
            if not merged_messages or merged_messages[-1]["role"] != message["role"]:
                merged_messages.append(message)
            else:
                merged_messages[-1]["content"].extend(message["content"])

        # if merged_messages and merged_messages[0]["role"] != Role.USER.value:
        #     merged_messages.insert(0, {"role": Role.USER.value, "content": []})

        return merged_messages

    def clear(self) -> None:
        self.messages = []

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
