from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Union

from nonebot import get_driver
from nonebot.adapters import Bot, Event
from nonebot.message import event_preprocessor

nonebot_run_time: datetime = datetime.now().astimezone()
bot_connect_time: Dict[str, datetime] = {}
recv_num: Dict[str, int] = {}
send_num: Dict[str, int] = {}

driver = get_driver()

SEND_APIS: Dict[str, Union[List[str], Callable[[str], bool]]] = {
    # "BilibiliLive": [],  # 狗东西发消息不走 call_api
    "Console": ["send_msg"],
    "Ding": ["send"],
    "Discord": ["create_message"],
    "Feishu": ["im/v1/messages"],
    "Kaiheila": ["message_create", "directMessage_create"],
    "Minecraft": ["send_msg"],
    "mirai2": ["send_friend_message", "send_group_message", "send_temp_message"],
    "ntchat": lambda x: x.startswith("send_"),
    "OneBot V11": ["send_private_msg", "send_group_msg", "send_msg"],
    "OneBot V12": ["send_message"],
    "QQ": [
        "post_dms_messages",
        "post_messages",
        "post_c2c_messages",
        "post_c2c_files",
        "post_group_messages",
        "post_group_files",
    ],
    "RedProtocol": ["send_message", "send_fake_forward"],
    "Satori": ["message_create"],
    "Telegram": lambda x: x.startswith("send_"),
    "大别野": ["send_message"],
}


def method_is_send_msg(platform: str, name: str) -> bool:
    return (platform in SEND_APIS) and (
        (name in it) if isinstance((it := SEND_APIS[platform]), list) else it(name)
    )


@Bot.on_called_api
async def called_api(
    bot: Bot,
    exc: Optional[Exception],
    api: str,
    _: Dict[str, Any],
    __: Any,
):
    if (not exc) and method_is_send_msg(bot.adapter.get_name(), api):
        send_num[bot.self_id] += 1


@driver.on_bot_connect
async def _(bot: Bot):
    bot_connect_time[bot.self_id] = datetime.now().astimezone()
    recv_num[bot.self_id] = 0
    if bot.adapter.get_name() in SEND_APIS:
        send_num[bot.self_id] = 0


@driver.on_bot_disconnect
async def _(bot: Bot):
    bot_connect_time.pop(bot.self_id, None)
    recv_num.pop(bot.self_id, None)
    send_num.pop(bot.self_id, None)


@event_preprocessor
async def _(bot: Bot, event: Event):
    if event.get_type() == "message":
        recv_num[bot.self_id] += 1
