from datetime import datetime
from typing import Optional

from nonebot import get_driver

bot_connect_time: Optional[datetime]
nonebot_run_time: Optional[datetime]

driver = get_driver()


@driver.on_startup
def _():
    global nonebot_run_time
    nonebot_run_time = datetime.now()


@driver.on_bot_connect
def _():
    global bot_connect_time
    bot_connect_time = datetime.now()


def get_nonebot_run_time():
    try:
        return nonebot_run_time
    except:
        return None


def get_bot_connect_time():
    try:
        return bot_connect_time
    except:
        return None
