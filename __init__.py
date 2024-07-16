# Python Official
import random
from typing import List, Dict

# Nonebot
from nonebot import logger, get_plugin_config, on_message, on_command
from nonebot.adapters.onebot.v11 import (
    Message as OnebotMessage,
    MessageSegment as OnebotMessageSegment,
)
from nonebot.adapters.onebot.v11.event import GroupMessageEvent
from nonebot.plugin import PluginMetadata
from nonebot.rule import to_me

# Local
from .config import Config
from .utils import url_to_base64, basic_call_api, Role, Model


__plugin_meta__ = PluginMetadata(
    name="ChatGPT",
    description="通过api与ChatGPT模型进行对话",
    usage="""
    ask: 与ChatGPT模型进行对话
    clr: 清空对话历史
    cgm: 查看当前群聊的对话历史
    或者直接at机器人进行对话
    """,
    type="application",
    config=Config,
    supported_adapters={"~onebot.v11", "~qq"},
    extra={
        "author": "loss0fTime",
    },
)


plugin_config = get_plugin_config(Config)

model_used: Model = Model(plugin_config.chatgpt_model)  # 转换为枚举类型


def call_api(model: Model, messages: List[dict]) -> tuple[int, str]:
    return basic_call_api(
        model,
        messages,
        plugin_config.chatgpt_api_key,
        plugin_config.chatgpt_api_url,
        plugin_config.chatgpt_max_tokens,
        logger,
    )


class GroupMessageHistory:
    def __init__(self, max_message_num: int):
        self.length = 0
        self.max_message_num = max_message_num
        self.messages: List[dict] = []

    def append_message(self, message: dict) -> None:
        if len(self.messages) >= self.max_message_num:
            self.messages.pop(0)
        self.messages.append(message)

    def get_messages(self) -> List[dict]:
        return self.messages

    def get_merged_messages(self) -> List[dict]:
        """
        将messages中连续的User消息合并为一条User消息
        """
        merged_messages = []
        for message in self.messages:
            if message["role"] == Role.USER.value:
                GroupMessageHistory.combine_user_messages(
                    merged_messages, message["content"]
                )
            else:
                merged_messages.append(message)
        return merged_messages

    def __str__(self) -> str:
        """
        输出各条消息
        每条消息最长20个字符，超过部分用...代替
        base64图片以[图片]代替
        """
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

    @staticmethod
    def combine_user_messages(messages: List[dict], new_content: List[dict]) -> None:
        if messages and messages[-1]["role"] == Role.USER.value:
            messages[-1]["content"].extend(new_content)
        else:
            messages.append({"role": Role.USER.value, "content": new_content})

        # messages: first message must use the "user" role
        if messages[-1]["role"] != Role.USER.value:
            messages.append({"role": Role.USER.value, "content": []})

    def clear(self) -> None:
        self.messages = []


call_bot = on_command("ask", priority=5, block=True)
at_bot = on_message(priority=5, block=True, rule=to_me())
random_reply = on_message(priority=99, block=False)

clear_messages = on_command("clr", priority=5, block=True)
check_group_messages = on_command("cgm", priority=5, block=True)

groups_message: Dict[int, GroupMessageHistory] = {}
id_to_card: dict[str, str] = {}


def clac_content_length(content: List[dict]) -> int:
    length = 0
    for segment in content:
        if segment["type"] == "text":
            length += len(segment["text"])
        elif segment["type"] == "image_url":
            # base64长度
            length += len(segment["image_url"]["url"])

    return length


async def generate_message(
    message: OnebotMessage | str, prefix: str = "", role: Role = Role.USER
) -> dict:
    if isinstance(message, str):
        message = OnebotMessage([OnebotMessageSegment.text(message)])

    text: str = prefix
    image_urls: List[str] = []
    for segment in message:
        segment: OnebotMessageSegment = segment
        if segment.is_text():
            text += segment.data.get("text", "")
        elif segment.type == "image":
            image_urls.append(segment.data.get("url", ""))
        elif segment.type == "at":
            at_qq: str = str(segment.data.get("qq", 0))
            if (card := id_to_card.get(at_qq, None)) != None:
                text += f"@{card} "
            # logger.debug(f"at_qq: {at_qq}, card: {card}")

    content: List[dict] = []
    content.append({"type": "text", "text": text})
    for url in image_urls:
        base64_image = await url_to_base64(url)
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
            }
        )

    return {
        "role": role.value,
        "content": content,
    }


async def handle_message(
    event: GroupMessageEvent, append_prompt: bool = False, skip: bool = False
):

    # 初始化
    group_id: int = event.group_id
    if group_id not in groups_message:
        groups_message[group_id] = GroupMessageHistory(
            plugin_config.chatgpt_max_message_num
        )
    g_messages = groups_message[group_id]
    user_id: str = event.get_user_id()
    nickname: str = event.sender.nickname  # QQ昵称
    card: str = event.sender.card  # 群名片
    role: Role = Role.USER

    # 新消息处理
    logger.debug(f"User ID: {user_id}, Nickname: {nickname}, Card: {card}")
    if card == None or card == "":
        card = nickname
    id_to_card[user_id] = card  # 记录用户的群名片，用于处理at

    if user_id == plugin_config.chatgpt_bot_id:
        skip = True
        role = Role.ASSISTANT

    new_messages = await generate_message(
        event.get_message(), prefix=f"{card}: ", role=role
    )
    g_messages.append_message(new_messages)

    # logger.debug(f"Length: {len(g_messages.get_messages())}")

    # API调用
    if skip:
        return

    if append_prompt:
        new_messages = [
            await generate_message(plugin_config.chatgpt_prompt, role=Role.SYSTEM)
        ]
        new_messages.extend(g_messages.get_messages())
    else:
        new_messages = g_messages.get_messages()

    # 调用API
    code, response = await call_api(model_used, new_messages)

    # 拼接回复消息
    g_messages.append_message(await generate_message(response, role=Role.ASSISTANT))

    if code == 1:
        g_messages.clear()

    logger.debug(f"要回复的消息: {response}")
    return response


@call_bot.handle()
async def call_bot_handle(event: GroupMessageEvent):
    response = await handle_message(event, append_prompt=True)
    await call_bot.finish(response)


@at_bot.handle()
async def at_bot_handle(event: GroupMessageEvent):
    response = await handle_message(event, append_prompt=True)
    await at_bot.finish(response)


@random_reply.handle()
async def random_reply_handle(event: GroupMessageEvent):
    skip: bool = False
    group_id: int = event.group_id
    if plugin_config.chatgpt_enable_random_reply == False:
        skip = True
        logger.debug("Random reply is disabled")
    elif int(group_id) not in plugin_config.chatgpt_random_reply_whitelist:
        skip = True
        logger.debug("Group not in whitelist")
    elif random.randint(0, 99) >= plugin_config.chatgpt_random_reply_percentage:
        skip = True
        logger.debug("Random reply percentage not reached")
    response = await handle_message(event, append_prompt=True, skip=skip)
    await random_reply.finish(response)


@clear_messages.handle()
async def clear_messages_handle(event: GroupMessageEvent):
    group_id: int = event.group_id
    if group_id in groups_message:
        groups_message[group_id].clear()
        await clear_messages.finish("对话历史已清空！")


@check_group_messages.handle()
async def check_group_messages_handle(event: GroupMessageEvent):
    group_id: int = event.group_id
    if group_id in groups_message:
        g_messages = groups_message[group_id]
        await check_group_messages.finish(str(g_messages))
    else:
        await check_group_messages.finish("当前群聊无消息记录！")
