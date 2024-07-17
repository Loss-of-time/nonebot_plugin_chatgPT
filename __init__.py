# __init__.py

from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata

from .config import Config
from .handlers import register_handlers
from .models import GroupMessageHistory, groups_message, id_to_card

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

# Initialize handlers
register_handlers()