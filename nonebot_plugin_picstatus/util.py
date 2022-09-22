import json
from datetime import timedelta
from io import BytesIO

import aiofiles
from PIL import Image
from aiohttp import ClientSession


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
        "https://www.dmoe.cc/random.php?return=json", is_text=True
    )
    return await async_request(json.loads(r)["imgurl"])


async def get_qq_avatar(qq):
    return await async_request(f"https://q2.qlogo.cn/headimg_dl?dst_uin={qq}&spec=640")


async def async_open_img(fp, *args, **kwargs) -> Image.Image:
    async with aiofiles.open(fp, "rb") as f:
        p = BytesIO(await f.read())
    return Image.open(p, *args, **kwargs)
