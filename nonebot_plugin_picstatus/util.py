import json
import re
from datetime import timedelta
from io import BytesIO
from pathlib import Path
from typing import List, Literal, Optional, Union, cast, overload

import anyio
from httpx import AsyncClient
from nonebot import logger
from nonebot.adapters import Bot
from PIL import Image

from .config import config

try:
    from nonebot.adapters.onebot.v11 import Bot as OBV11Bot
except ImportError:
    OBV11Bot = None

try:
    from nonebot.adapters.telegram import Bot as TGBot
except ImportError:
    TGBot = None


def format_timedelta(t: timedelta):
    mm, ss = divmod(t.seconds, 60)
    hh, mm = divmod(mm, 60)
    s = f"{hh}:{mm:02d}:{ss:02d}"
    if t.days:
        s = f"{t.days}天 {s}"
    # if t.microseconds:
    #     s += f" {t.microseconds / 1000:.3f}毫秒"
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


async def async_open_img(
    fp: Union[str, Path, anyio.Path],
    *args,
    **kwargs,
) -> Image.Image:
    p = BytesIO(await anyio.Path(fp).read_bytes())
    return Image.open(p, *args, **kwargs)


def format_byte_count(b: int) -> str:
    units = ["B", "K", "M", "G", "T", "P", "E", "Z", "Y"]
    multiplier = 1024

    value = b
    for unit in units:
        if value < multiplier:
            return f"{value:.2f}{unit}"
        value /= multiplier

    return f"{value:.2f}{units[-1]}"


def match_list_regexp(reg_list: List[str], txt: str) -> Optional[re.Match]:
    return next((match for r in reg_list if (match := re.search(r, txt))), None)


def process_text_len(text: str) -> str:
    real_max_len = config.ps_max_text_len - 3
    if len(text) > real_max_len:
        text = f"{text[:real_max_len]}..."
    return text


async def download_telegram_file(bot: Bot, file_id: str) -> bytes:
    assert TGBot and isinstance(bot, TGBot), "仅 Telegram Bot 可调用此函数"

    res = await bot.get_file(file_id=file_id)
    file_path = cast(str, res.file_path)

    if await (p := anyio.Path(file_path)).exists():
        return await p.read_bytes()

    url = f"{bot.bot_config.api_server}file/bot{bot.bot_config.token}/{file_path}"
    return await async_request(url, proxy=config.proxy)


async def get_qq_avatar(qq) -> bytes:
    return await async_request(f"https://q2.qlogo.cn/headimg_dl?dst_uin={qq}&spec=640")


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
    except Exception:
        logger.exception("获取Bot头像失败，使用默认头像替代")

    if avatar:
        return Image.open(BytesIO(avatar))

    return await async_open_img(config.ps_default_avatar)
