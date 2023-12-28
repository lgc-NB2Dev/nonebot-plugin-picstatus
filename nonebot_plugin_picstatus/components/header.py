import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

import psutil
from nonebot import get_bots, logger
from nonebot.adapters import Bot as BaseBot
from nonebot.adapters import Event as BaseEvent
from nonebot.matcher import current_bot
from nonebot.message import event_preprocessor
from nonebot_plugin_userinfo import UserInfo, get_user_info
from playwright.async_api import Request, Route
from yarl import URL

from ..config import DEFAULT_AVATAR_PATH, config
from ..render import ENVIRONMENT, ROUTE_URL, router
from ..statistics import bot_connect_time, nonebot_run_time, recv_num, send_num
from ..util import format_timedelta, guess_mime_from_bytes
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
    nick: str
    bot_connected: str
    msg_rec: str
    msg_sent: str


@dataclass
class HeaderData:
    bots: List[BotStatus]
    nb_run: str
    booted: str


async def get_bot_status(bot: BaseBot, now_time: datetime) -> BotStatus:
    msg_rec: Optional[str] = None
    msg_sent: Optional[str] = None

    if OBV11Bot and isinstance(bot, OBV11Bot):
        try:
            bot_stat = (await bot.get_status()).get("stat")
        except AttributeError:
            bot_stat = None

        if bot_stat:
            msg_rec = bot_stat.get("message_received") or bot_stat.get(
                "MessageReceived",
            )
            msg_sent = bot_stat.get("message_sent") or bot_stat.get("MessageSent")

    if msg_rec is None:
        num = recv_num.get(bot.self_id)
        msg_rec = "未知" if num is None else str(num)
    if msg_sent is None:
        num = send_num.get(bot.self_id)
        msg_sent = "未知" if num is None else str(num)

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

    return BotStatus(
        self_id=bot.self_id,
        nick=nick,
        bot_connected=bot_connected,
        msg_rec=msg_rec,
        msg_sent=msg_sent,
    )


async def get_header_data() -> HeaderData:
    now_time = datetime.now()
    bots = (
        [await get_bot_status(current_bot.get(), now_time)]
        if config.ps_show_current_bot_only
        else await asyncio.gather(
            *(get_bot_status(bot, now_time) for bot in get_bots().values()),
        )
    )
    nb_run = format_timedelta(now_time - nonebot_run_time) if nonebot_run_time else "未知"
    booted = format_timedelta(
        now_time - datetime.fromtimestamp(psutil.boot_time()),
    )
    return HeaderData(bots=bots, nb_run=nb_run, booted=booted)


@event_preprocessor
async def _(bot: BaseBot, event: BaseEvent):
    if bot.self_id in bot_info_cache:
        return
    try:
        info = await get_user_info(bot, event, bot.self_id)
    except Exception as e:
        logger.warning(f"Error when getting bot info: {e.__class__.__name__}: {e}")
        return
    if info:
        bot_info_cache[bot.self_id] = info


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
    await route.fulfill(content_type=guess_mime_from_bytes(data), body=data)


@register_component
async def header():
    return await ENVIRONMENT.get_template("header.html.jinja").render_async(
        data=await get_header_data(),
    )
