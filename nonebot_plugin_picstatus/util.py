import json
import platform
import re
from datetime import timedelta
from io import BytesIO

import aiofiles
from PIL import Image
from aiohttp import ClientSession
from nonebot import logger


def format_timedelta(t: timedelta):
    mm, ss = divmod(t.seconds, 60)
    hh, mm = divmod(mm, 60)
    s = "%d:%02d:%02d" % (hh, mm, ss)
    if t.days:
        s = ("%d天 " % t.days) + s
    # if t.microseconds:
    #     s += " %.3f 毫秒" % (t.microseconds / 1000)
    return s


async def async_request(url, *args, is_text=False, **kwargs):
    async with ClientSession() as c:
        async with c.get(url, *args, **kwargs) as r:
            return (await r.text()) if is_text else (await r.read())


async def get_anime_pic():
    r: str = await async_request(
        "https://api.gmit.vip/Api/DmImg?format=json", is_text=True
    )
    return await async_request(json.loads(r)["data"]["url"])


async def get_qq_avatar(qq):
    return await async_request(f"https://q2.qlogo.cn/headimg_dl?dst_uin={qq}&spec=640")


async def async_open_img(fp, *args, **kwargs) -> Image.Image:
    async with aiofiles.open(fp, "rb") as f:
        p = BytesIO(await f.read())
    return Image.open(p, *args, **kwargs)


async def get_system_name():
    system, _, release, version, machine, _ = platform.uname()
    system, release, version = platform.system_alias(system, release, version)

    if system == "Java":
        _, _, _, (system, release, machine) = platform.java_ver()

    if system == "Darwin":
        return f"MacOS {platform.mac_ver()[0]} {machine}"
    if system == "Windows":
        return f"Windows {release} {platform.win32_edition()} {machine}"
    if system == "Linux":
        try:
            async with aiofiles.open("/etc/issue") as f:
                v: str = await f.read()
        except:
            logger.exception("读取 /etc/issue 文件失败")
            v = f"未知Linux {release}"
        else:
            v = v.replace(r"\n", "").replace(r"\l", "").strip()
        return f"{v} {machine}"
    else:
        return f"{system} {release}"


def format_byte_count(b: int):
    if (k := b / 1024) < 1:
        return f"{b}B"
    if (m := k / 1024) < 1:
        return f"{k:.2f}K"
    if (g := m / 1024) < 1:
        return f"{m:.2f}M"
    return f"{g:.2f}G"


def match_list_regexp(reg_list, txt):
    for r in reg_list:
        if m := re.search(r, txt):
            return m
