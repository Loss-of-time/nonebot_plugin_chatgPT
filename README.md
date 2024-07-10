# ChatGpt插件

## 功能

基于Nonebot2与Onebot协议
使用api连接群聊消息和ChatGpt聊天

## 安装与使用

### 安装

暂无

### 配置项

配置请参考`config.py`文件

```py
chatgpt_api_key: str
"""The api key of chatgpt"""

chatgpt_bot_id: int = 0
"""The qq id of bot"""

chatgpt_api_url: str = "https://api.openai.com/v1/"

chatgpt_max_message_num: int = 8

chatgpt_model: str = "gpt-4o"

chatgpt_prompt: str = PROMPT
"""The initial system prompt of chatgpt"""

chatgpt_enable_random_reply: bool = False
"""Whether to enable random reply"""

chatgpt_random_reply_whitelist: list[str] = [""]

chatgpt_random_reply_percentage: int = 20
```
