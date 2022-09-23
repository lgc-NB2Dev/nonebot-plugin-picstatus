from datetime import datetime
from typing import Dict, Optional

from nonebot import get_driver
from nonebot.adapters.onebot.v11 import Bot

bot_connect_time: Dict[str, datetime] = {}
nonebot_run_time: Optional[datetime]

driver = get_driver()


@driver.on_startup
def _():
    global nonebot_run_time
    nonebot_run_time = datetime.now()


@driver.on_bot_connect
def _(bot: Bot):
    global bot_connect_time
    bot_connect_time[bot.self_id] = datetime.now()


def get_nonebot_run_time():
    try:
        return nonebot_run_time
    except:
        return None


def get_bot_connect_time(bot_id):
    return bot_connect_time.get(bot_id)
