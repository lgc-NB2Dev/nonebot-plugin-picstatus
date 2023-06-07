import json
import re
from datetime import timedelta
from io import BytesIO
from typing import List, Literal, Optional, cast, overload

import anyio
from httpx import AsyncClient
from nonebot import logger
from nonebot.internal.adapter import Bot
from PIL import Image

from .config import config
from .const import DEFAULT_AVATAR_PATH

try:
    from nonebot.adapters.onebot.v11 import Bot as OBV11Bot
except:
    OBV11Bot = None

try:
    from nonebot.adapters.telegram import Bot as TGBot
except:
    TGBot = None


def format_timedelta(t: timedelta):
    mm, ss = divmod(t.seconds, 60)
    hh, mm = divmod(mm, 60)
    s = "%d:%02d:%02d" % (hh, mm, ss)
    if t.days:
        s = ("%d天 " % t.days) + s
    # if t.microseconds:
    #     s += " %.3f 毫秒" % (t.microseconds / 1000)
    return s


@overload
async def async_request(
    url: str,
    *args,
    is_text: Literal[False] = False,
    proxy: Optional[str] = None,
    **kwargs,
) -> bytes:
    ...


@overload
async def async_request(
    url: str,
    *args,
    is_text: Literal[True] = True,
    proxy: Optional[str] = None,
    **kwargs,
) -> str:
    ...


async def async_request(url: str, *args, is_text=False, proxy=None, **kwargs):
    async with AsyncClient(
        proxies=proxy,
        follow_redirects=True,
        timeout=config.ps_req_timeout,
    ) as cli:
        res = await cli.get(url, *args, **kwargs)
        return res.text if is_text else res.content


async def get_anime_pic() -> bytes:
    data = json.loads(
        await async_request("https://api.gumengya.com/Api/DmImg", is_text=True),
    )
    assert str(data.get("code")) == "200"
    return await async_request(data["data"]["url"])


async def get_qq_avatar(qq) -> bytes:
    return await async_request(f"https://q2.qlogo.cn/headimg_dl?dst_uin={qq}&spec=640")


async def async_open_img(fp, *args, **kwargs) -> Image.Image:
    async with (await anyio.open_file(fp, "rb")) as f:
        p = BytesIO(await f.read())
    return Image.open(p, *args, **kwargs)


def format_byte_count(b: int) -> str:
    if (k := b / 1024) < 1:
        return f"{b}B"
    if (m := k / 1024) < 1:
        return f"{k:.2f}K"
    if (g := m / 1024) < 1:
        return f"{m:.2f}M"
    return f"{g:.2f}G"


def match_list_regexp(reg_list: List[str], txt: str) -> Optional[re.Match]:
    for r in reg_list:
        if m := re.search(r, txt):
            return m
    return None


def process_text_len(text: str) -> str:
    real_max_len = config.ps_max_text_len - 3
    if len(text) > real_max_len:
        text = f"{text[:real_max_len]}..."

    return text  # noqa: RET504


async def download_telegram_file(bot: Bot, file_id: str) -> bytes:
    assert TGBot and isinstance(bot, TGBot), "仅 Telegram Bot 可调用此函数"

    res = await bot.get_file(file_id=file_id)
    file_path = cast(str, res.file_path)

    if await (p := anyio.Path(file_path)).exists():
        return await p.read_bytes()

    url = f"{bot.bot_config.api_server}file/bot{bot.bot_config.token}/{file_path}"
    return await async_request(url, proxy=config.proxy)


async def get_tg_avatar(bot: Bot) -> bytes:
    assert TGBot and isinstance(bot, TGBot), "仅 Telegram Bot 可调用此函数"

    res = await bot.get_user_profile_photos(user_id=int(bot.self_id), limit=1)
    file_id = res.photos[0][-1].file_id

    return await download_telegram_file(bot, file_id)


async def get_bot_avatar(bot: Bot) -> Image.Image:
    avatar = None

    try:
        if OBV11Bot and isinstance(bot, OBV11Bot):
            avatar = await get_qq_avatar(bot.self_id)
        elif TGBot and isinstance(bot, TGBot):
            avatar = await get_tg_avatar(bot)
        else:
            logger.info("暂不支持获取该平台Bot头像，使用默认头像替代")
    except:
        logger.exception("获取Bot头像失败，使用默认头像替代")

    if avatar:
        return Image.open(BytesIO(avatar))

    return await async_open_img(DEFAULT_AVATAR_PATH)
