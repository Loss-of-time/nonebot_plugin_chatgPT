# handlers.py

import random
from typing import List
from nonebot import on_command, on_message, logger, get_plugin_config
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import Message as OnebotMessage, MessageSegment as OnebotMessageSegment
from nonebot.adapters.onebot.v11.event import GroupMessageEvent

from .config import Config
from .models import Role, Model, GroupMessageHistory, groups_message, id_to_card
from .utils import call_api, url_to_base64

plugin_config = get_plugin_config(Config)
model_used: Model = Model(plugin_config.chatgpt_model)

async def generate_message(message: OnebotMessage | str, prefix: str = "", role: Role = Role.USER) -> dict:
    if isinstance(message, str):
        message = OnebotMessage([OnebotMessageSegment.text(message)])

    text: str = prefix
    image_urls: List[str] = []
    for segment in message:
        if segment.is_text():
            text += segment.data.get("text", "")
        elif segment.type == "image":
            image_urls.append(segment.data.get("url", ""))
        elif segment.type == "at":
            at_qq: str = str(segment.data.get("qq", 0))
            if (card := id_to_card.get(at_qq, None)) is not None:
                text += f"@{card} "

    content: List[dict] = [{"type": "text", "text": text}]
    for url in image_urls:
        base64_image = await url_to_base64(url)
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
            }
        )

    return {"role": role.value, "content": content}

async def handle_message(event: GroupMessageEvent, append_prompt: bool = False, skip: bool = False) -> str:
    group_id: int = event.group_id
    if group_id not in groups_message:
        groups_message[group_id] = GroupMessageHistory(plugin_config.chatgpt_max_message_num)
    g_messages = groups_message[group_id]
    user_id: str = event.get_user_id()
    nickname: str = event.sender.nickname
    card: str = event.sender.card or nickname
    role: Role = Role.USER

    logger.debug(f"User ID: {user_id}, Nickname: {nickname}, Card: {card}")
    id_to_card[user_id] = card

    if user_id == str(plugin_config.chatgpt_bot_id):
        skip = True
        role = Role.ASSISTANT

    new_messages = await generate_message(event.get_message(), prefix=f"{card}: ", role=role)
    g_messages.append_message(new_messages)

    if skip:
        return ""

    messages = g_messages.get_merged_messages() if model_used == Model.CLAUDE else g_messages.get_messages()
    if append_prompt:
        new_messages = [await generate_message(plugin_config.chatgpt_prompt, role=Role.SYSTEM)] + messages
    else:
        new_messages = messages

    code, response = await call_api(model_used, new_messages, plugin_config.chatgpt_api_key, plugin_config.chatgpt_api_url, plugin_config.chatgpt_max_tokens, logger)

    g_messages.append_message(await generate_message(response, role=Role.ASSISTANT))

    if code == 1:
        g_messages.clear()

    logger.debug(f"要回复的消息: {response}")
    return str(response)

def register_handlers():
    call_bot = on_command("ask", priority=5, block=True)
    at_bot = on_message(priority=5, block=True, rule=to_me())
    random_reply = on_message(priority=99, block=False)
    clear_messages = on_command("clr", priority=5, block=True)
    check_group_messages = on_command("cgm", priority=5, block=True)

    @call_bot.handle()
    async def call_bot_handle(event: GroupMessageEvent):
        response = await handle_message(event, append_prompt=True)
        for resp in response.split("¦"):
            await call_bot.send(resp)

    @at_bot.handle()
    async def at_bot_handle(event: GroupMessageEvent):
        response = await handle_message(event, append_prompt=True)
        for resp in response.split("¦"):
            await at_bot.send(resp)

    @random_reply.handle()
    async def random_reply_handle(event: GroupMessageEvent):
        for segment in event.get_message():
            if segment.type == "text" and "暂不支持该消息类型" in segment.data.get("text", ""):
                logger.debug("暂不支持该消息类型")
                return

        skip = not plugin_config.chatgpt_enable_random_reply or \
               event.group_id not in plugin_config.chatgpt_random_reply_whitelist or \
               random.randint(0, 99) >= plugin_config.chatgpt_random_reply_percentage

        response = await handle_message(event, append_prompt=True, skip=skip)
        if not skip:
            for resp in response.split("¦"):
                await random_reply.send(resp)

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
            await check_group_messages.finish(str(groups_message[group_id]))
        else:
            await check_group_messages.finish("当前群聊无消息记录！")