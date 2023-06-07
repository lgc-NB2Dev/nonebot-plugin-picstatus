from datetime import datetime
from typing import Dict, Optional

from nonebot import get_driver, on_message
from nonebot.internal.adapter import Bot

try:
    from nonebot.adapters.onebot.v11 import Bot as OneBotV11Bot
except ImportError:
    OneBotV11Bot = None

bot_connect_time: Dict[str, datetime] = {}
nonebot_run_time: datetime = datetime.now()
recv_num: Dict[str, int] = {}
send_num: Dict[str, int] = {}

driver = get_driver()


def method_is_send_msg(platform: str, name: str) -> bool:
    if platform == "Telegram":
        return name.startswith("send")
    return False


async def called_api(bot: Bot, exc: Optional[Exception], api: str, _, __):
    if (not exc) and method_is_send_msg(bot.adapter.get_name(), api):
        num = send_num.get(bot.self_id, 0)
        send_num[bot.self_id] = num + 1


async def not_ob_v11_bot_rule(bot: Bot) -> bool:
    return not (OneBotV11Bot and isinstance(bot, OneBotV11Bot))


@driver.on_bot_connect
async def _(bot: Bot):
    bot_id = bot.self_id
    bot_connect_time[bot_id] = datetime.now()

    if bot_id not in send_num:
        send_num[bot_id] = 0
        recv_num[bot_id] = 0

    if await not_ob_v11_bot_rule(bot):
        bot.on_called_api(called_api)


mat_rec = on_message(block=False, rule=not_ob_v11_bot_rule)


@mat_rec.handle()
async def _(bot: Bot):
    num = recv_num.get(bot.self_id, 0)
    recv_num[bot.self_id] = num + 1
