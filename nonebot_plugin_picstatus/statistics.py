from datetime import datetime
from typing import Dict, Optional

from nonebot import get_driver
from nonebot.adapters import Bot, Event
from nonebot.message import event_preprocessor

nonebot_run_time: datetime = datetime.now()
bot_connect_time: Dict[str, datetime] = {}
recv_num: Dict[str, int] = {}
send_num: Dict[str, int] = {}

driver = get_driver()


def get_bot_id(bot: Bot) -> str:
    return f"{bot.adapter.get_name()}:{bot.self_id}"


def method_is_send_msg(platform: str, name: str) -> bool:
    if platform == "OneBot V11":
        return name.startswith("send_")
    if platform == "Telegram":
        return name.startswith("send")
    return False


async def called_api(bot: Bot, exc: Optional[Exception], api: str, _, __):
    if (not exc) and method_is_send_msg(bot.adapter.get_name(), api):
        bot_id = get_bot_id(bot)
        num = send_num.get(bot_id, 0) + 1
        send_num[bot_id] = num


@driver.on_bot_connect
async def _(bot: Bot):
    bot_id = get_bot_id(bot)
    bot_connect_time[bot_id] = datetime.now()
    recv_num[bot_id] = 0
    send_num[bot_id] = 0
    bot.on_called_api(called_api)


@driver.on_bot_disconnect
async def _(bot: Bot):
    bot_id = get_bot_id(bot)
    bot_connect_time.pop(bot_id, None)
    send_num.pop(bot_id, None)
    recv_num.pop(bot_id, None)


@event_preprocessor
async def _(bot: Bot, event: Event):
    if event.get_type() == "message":
        bot_id = get_bot_id(bot)
        num = recv_num.get(bot_id, 0)
        recv_num[bot_id] = num + 1
