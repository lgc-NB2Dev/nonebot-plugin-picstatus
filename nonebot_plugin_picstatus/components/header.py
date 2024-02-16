import asyncio
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import psutil
from nonebot import get_bots, logger
from nonebot.adapters import Bot as BaseBot, Event as BaseEvent
from nonebot.matcher import current_bot, current_event
from nonebot.message import event_preprocessor
from nonebot_plugin_userinfo import UserInfo, get_user_info
from playwright.async_api import Request, Route
from yarl import URL

from ..config import DEFAULT_AVATAR_PATH, config
from ..render import ENVIRONMENT, ROUTE_URL, router
from ..statistics import bot_connect_time, nonebot_run_time, recv_num, send_num
from ..util import format_timedelta
from . import register_component

try:
    from nonebot.adapters.onebot.v11 import Bot as OBV11Bot
except ImportError:
    OBV11Bot = None


bot_info_cache: Dict[str, UserInfo] = {}
bot_avatar_cache: Dict[str, bytes] = {}


@dataclass
class BotStatus:
    self_id: str
    adapter: str
    nick: str
    bot_connected: str
    msg_rec: str
    msg_sent: str


@dataclass
class HeaderData:
    bots: List[BotStatus]
    nb_run: str
    booted: str


async def get_ob11_msg_num(bot: BaseBot) -> Tuple[Optional[int], Optional[int]]:
    if not (config.ps_ob_v11_use_get_status and OBV11Bot and isinstance(bot, OBV11Bot)):
        return None, None

    try:
        bot_stat = (await bot.get_status()).get("stat")
    except Exception as e:
        logger.warning(
            f"Error when getting bot status: {e.__class__.__name__}: {e}",
        )
        return None, None
    if not bot_stat:
        return None, None

    msg_rec = bot_stat.get("message_received") or bot_stat.get(
        "MessageReceived",
    )
    msg_sent = bot_stat.get("message_sent") or bot_stat.get("MessageSent")
    return msg_rec, msg_sent


async def get_bot_status(bot: BaseBot, now_time: datetime) -> BotStatus:
    nick = (
        ((info := bot_info_cache[bot.self_id]).user_displayname or info.user_name)
        if (not config.ps_use_env_nick) and (bot.self_id in bot_info_cache)
        else next(iter(config.nickname), None)
    ) or "Bot"
    bot_connected = (
        format_timedelta(now_time - t)
        if (t := bot_connect_time.get(bot.self_id))
        else "未知"
    )

    msg_rec, msg_sent = await get_ob11_msg_num(bot)
    if msg_rec is None:
        msg_rec = recv_num.get(bot.self_id)
    if msg_sent is None:
        msg_sent = send_num.get(bot.self_id)
    msg_rec = "未知" if (msg_rec is None) else str(msg_rec)
    msg_sent = "未知" if (msg_sent is None) else str(msg_sent)

    return BotStatus(
        self_id=bot.self_id,
        adapter=bot.adapter.get_name(),
        nick=nick,
        bot_connected=bot_connected,
        msg_rec=msg_rec,
        msg_sent=msg_sent,
    )


async def get_header_data() -> HeaderData:
    now_time = datetime.now().astimezone()
    bots = (
        [await get_bot_status(current_bot.get(), now_time)]
        if config.ps_show_current_bot_only
        else await asyncio.gather(
            *(get_bot_status(bot, now_time) for bot in get_bots().values()),
        )
    )
    nb_run = (
        format_timedelta(now_time - nonebot_run_time) if nonebot_run_time else "未知"
    )
    booted = format_timedelta(
        now_time - datetime.fromtimestamp(psutil.boot_time()).astimezone(),
    )
    return HeaderData(bots=bots, nb_run=nb_run, booted=booted)


async def cache_bot_info(bot: BaseBot, event: BaseEvent):
    if bot.self_id in bot_info_cache:
        return
    try:
        info = await get_user_info(bot, event, bot.self_id)
    except Exception as e:
        logger.warning(f"Error when getting bot info: {e.__class__.__name__}: {e}")
        return
    if info:
        bot_info_cache[bot.self_id] = info


event_preprocessor(cache_bot_info)


@router(f"{ROUTE_URL}/api/bot_avatar/*")
async def _(route: Route, request: Request):
    url = URL(request.url)
    self_id = url.parts[-1]

    if self_id in bot_avatar_cache:
        await route.fulfill(body=bot_avatar_cache[self_id])
        return

    if (self_id in bot_info_cache) and (avatar := bot_info_cache[self_id].user_avatar):
        try:
            img = await avatar.get_image()
        except Exception as e:
            logger.warning(
                f"Error when getting bot avatar, fallback to default: "
                f"{e.__class__.__name__}: {e}",
            )
        else:
            bot_avatar_cache[self_id] = img
            await route.fulfill(body=img)
            return

    data = (
        config.ps_default_avatar
        if config.ps_default_avatar.is_file()
        else DEFAULT_AVATAR_PATH
    ).read_bytes()
    await route.fulfill(body=data)


@register_component
async def header():
    with suppress(Exception):
        await cache_bot_info(current_bot.get(), current_event.get())
    return await ENVIRONMENT.get_template("header.html.jinja").render_async(
        data=await get_header_data(),
    )
