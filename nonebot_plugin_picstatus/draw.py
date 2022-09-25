import asyncio
import platform
import random
import time
from datetime import datetime
from io import BytesIO
from typing import Dict, List, Optional, Tuple, Union

import nonebot
import psutil
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from nonebot import logger
from nonebot.adapters.onebot.v11 import Bot
from psutil._common import sdiskio, sdiskusage, snetio  # noqa

from .config import config
from .const import DEFAULT_AVATAR_PATH, DEFAULT_BG_PATH, DEFAULT_FONT_PATH
from .statistics import (
    get_bot_connect_time,
    get_nonebot_run_time,
)
from .util import (
    async_open_img,
    async_request,
    format_byte_count,
    format_timedelta,
    get_anime_pic,
    get_qq_avatar,
    get_system_name,
    match_list_regexp,
)
from .version import __version__

GRAY_BG_COLOR = "#aaaaaaaa"
WHITE_BG_COLOR = config.ps_bg_color
WHITE_MASK_COLOR = config.ps_mask_color


def get_font(size: int):
    default = str(DEFAULT_FONT_PATH)
    if config.ps_font:
        try:
            return ImageFont.truetype(config.ps_font, size)
        except:
            logger.exception("加载自定义字体失败，使用默认字体")

    return ImageFont.truetype(default, size)


def get_usage_color(usage: float):
    usage = round(usage)
    if usage >= 90:
        return "orangered"
    elif usage >= 70:
        return "orange"
    else:
        return "lightgreen"


async def draw_header(bot: Bot):
    # 获取Bot头像
    try:
        avatar = await get_qq_avatar(bot.self_id)
        avatar = Image.open(BytesIO(avatar))
    except:
        logger.exception("获取Bot头像失败，使用默认头像替代")
        avatar = await async_open_img(DEFAULT_AVATAR_PATH)

    # bot状态信息
    bot_stat = (await bot.get_status()).get("stat")
    if bot_stat:
        msg_rec = (
            bot_stat.get("message_received") or bot_stat.get("MessageReceived") or "未知"
        )
        msg_sent = bot_stat.get("message_sent") or bot_stat.get("MessageSent") or "未知"
    else:
        msg_rec = msg_sent = "未知"

    nick = (
        list(config.nickname)[0]
        if config.ps_use_env_nick
        else (await bot.get_login_info())["nickname"]
    )
    bot_connected = (
        format_timedelta(datetime.now() - t)
        if (t := get_bot_connect_time(bot.self_id))
        else "未知"
    )
    nb_run = (
        format_timedelta(datetime.now() - t) if (t := get_nonebot_run_time()) else "未知"
    )

    # 系统启动时间
    booted = format_timedelta(
        datetime.now() - datetime.fromtimestamp(psutil.boot_time())
    )

    font_30 = get_font(30)
    font_80 = get_font(80)

    bg = Image.new("RGBA", (1200, 300), WHITE_BG_COLOR)
    bg_draw = ImageDraw.Draw(bg)

    # 圆形遮罩
    circle_mask = Image.new("RGBA", (250, 250), "#ffffff00")
    ImageDraw.Draw(circle_mask).ellipse((0, 0, 250, 250), fill="black")

    # 利用遮罩裁剪圆形图片
    avatar = avatar.convert("RGBA").resize((250, 250))
    bg.paste(avatar, (25, 25), circle_mask)

    # 标题
    bg_draw.text((300, 140), nick, "black", font_80, "ld")

    # 详细信息
    bg_draw.multiline_text(
        (300, 160),
        f"Bot已连接 {bot_connected} | 收 {msg_rec} | 发 {msg_sent}\nNoneBot运行 {nb_run} | 系统运行 {booted}",
        "black",
        font_30,
    )

    # 标题与详细信息的分隔线
    bg_draw.line((300, 150, 500, 150), GRAY_BG_COLOR, 3)

    return bg


async def draw_cpu_memory_usage():
    # 获取占用信息
    psutil.cpu_percent()
    await asyncio.sleep(0.1)
    cpu_percent = psutil.cpu_percent()  # async wait

    cpu_count = psutil.cpu_count(logical=False)
    cpu_count_logical = psutil.cpu_count()
    cpu_freq = psutil.cpu_freq()
    ram_stat = psutil.virtual_memory()
    swap_stat = psutil.swap_memory()

    font_70 = get_font(70)
    font_25 = get_font(25)

    bg = Image.new("RGBA", (1200, 550), WHITE_BG_COLOR)
    bg_draw = ImageDraw.Draw(bg)

    # 背景灰色圆环
    circle_bg = Image.new("RGBA", (300, 300), "#ffffff00")
    ImageDraw.Draw(circle_bg).arc((0, 0, 300, 300), 0, 360, GRAY_BG_COLOR, 30)
    bg.paste(circle_bg, (50, 50), circle_bg)
    bg.paste(circle_bg, (450, 50), circle_bg)
    bg.paste(circle_bg, (850, 50), circle_bg)

    # 画占用率圆环
    bg_draw.arc(
        (50, 50, 350, 350),
        -90,
        (3.6 * cpu_percent) - 90,
        get_usage_color(cpu_percent),
        30,
    )
    bg_draw.arc(
        (450, 50, 750, 350),
        -90,
        (3.6 * ram_stat.percent) - 90,
        get_usage_color(ram_stat.percent),
        30,
    )
    bg_draw.arc(
        (850, 50, 1150, 350),
        -90,
        (3.6 * swap_stat.percent) - 90,
        get_usage_color(swap_stat.percent),
        30,
    )

    # 写字
    bg_draw.text((200, 350), "CPU", "black", font_70, "ma")
    bg_draw.text((600, 350), "RAM", "black", font_70, "ma")
    bg_draw.text((1000, 350), "SWAP", "black", font_70, "ma")

    # 写占用率
    bg_draw.text((200, 200), f"{cpu_percent:.0f}%", "black", font_70, "mm")
    bg_draw.text((600, 200), f"{ram_stat.percent:.0f}%", "black", font_70, "mm")
    bg_draw.text(
        (1000, 200),
        f"{swap_stat.percent:.0f}%" if swap_stat.total > 0 else "未部署",
        "black",
        font_70,
        "mm",
    )

    # 写详细信息
    # CPU
    if cpu_freq.max == 0:
        if cpu_freq.current == 0:
            freq_t = "主频未知"
        else:
            freq_t = f"当前 {cpu_freq.current:.0f}MHz"
    elif cpu_freq.max == cpu_freq.current:
        freq_t = f"最大 {cpu_freq.max:.0f}MHz"
    else:
        freq_t = f"{cpu_freq.current:.0f}MHz / {cpu_freq.max:.0f}MHz"
    bg_draw.text(
        (200, 470),
        f"{cpu_count}核 {cpu_count_logical}线程",
        "darkslategray",
        font_25,
        "ms",
    )
    bg_draw.text(
        (200, 500),
        freq_t,
        "darkslategray",
        font_25,
        "ms",
    )

    # RAM
    bg_draw.text(
        (600, 470),
        f"已用 {ram_stat.used / 1024 / 1024:.2f}M",
        "darkslategray",
        font_25,
        "ms",
    )
    bg_draw.text(
        (600, 500),
        f"空闲 {(ram_stat.total - ram_stat.used) / 1024 / 1024:.2f}M",
        "darkslategray",
        font_25,
        "ms",
    )

    # SWAP
    swap_used_t = (
        f"{swap_stat.used / 1024 / 1024:.2f}M" if swap_stat.total > 0 else "未知"
    )
    swap_free_t = (
        f"{(swap_stat.total - swap_stat.used) / 1024 / 1024:.2f}M"
        if swap_stat.total > 0
        else "未知"
    )
    bg_draw.text(
        (1000, 470),
        f"已用 {swap_used_t}",
        "darkslategray",
        font_25,
        "ms",
    )
    bg_draw.text(
        (1000, 500),
        f"空闲 {swap_free_t}",
        "darkslategray",
        font_25,
        "ms",
    )

    return bg


async def draw_disk_usage():
    disks = {}
    io_rw = {}

    font_45 = get_font(45)
    font_40 = get_font(40)

    async def get_disk_usage():
        """获取磁盘占用，返回左边距"""
        lp = 0  # 没办法，没办法给外层变量赋值

        # 获取磁盘状态
        for _d in psutil.disk_partitions():
            # 忽略分区
            if _r := match_list_regexp(config.ps_ignore_parts, _d.mountpoint):
                logger.info(f"空间读取 分区 {_d.mountpoint} 匹配 {_r.re.pattern}，忽略")
                continue

            # 根据盘符长度计算左侧留空长度用于写字
            s = font_45.getlength(_d.mountpoint) + 25
            if s > lp:
                lp = s

            try:
                disks[_d.mountpoint] = psutil.disk_usage(_d.mountpoint)
            except Exception as e:
                logger.exception(f"读取 {_d.mountpoint} 占用失败")
                if not config.ps_ignore_bad_parts:
                    disks[_d.mountpoint] = e

        return lp

    async def get_disk_io():
        """获取磁盘IO"""
        io1: Dict[str, sdiskio] = psutil.disk_io_counters(True)
        await asyncio.sleep(1)
        io2: Dict[str, sdiskio] = psutil.disk_io_counters(True)

        for _k, _v in io1.items():
            # 忽略分区
            if _r := match_list_regexp(config.ps_ignore_disk_ios, _k):
                logger.info(f"IO统计 磁盘 {_k} 匹配 {_r.re.pattern}，忽略")
                continue

            _r = io2[_k].read_bytes - _v.read_bytes
            _w = io2[_k].write_bytes - _v.write_bytes

            if _r == 0 and _w == 0 and config.ps_ignore_no_io_disk:
                logger.info(f"IO统计 忽略无IO磁盘 {_k}")
                continue

            io_rw[_k] = (format_byte_count(_r), format_byte_count(_w))

    left_padding, _ = await asyncio.gather(get_disk_usage(), get_disk_io())

    # 列表为空直接返回
    if not (disks or io_rw):
        return

    # 计算图片高度，创建背景图
    count = len(disks) + len(io_rw)
    bg = Image.new(
        "RGBA",
        (
            1200,
            100  # 上下边距
            + (50 * count)  # 每行磁盘/IO统计
            + (25 * (count - 1))  # 间隔
            + (10 if disks and io_rw else 0),  # 磁盘统计与IO统计间的间距
        ),
        WHITE_BG_COLOR,
    )
    bg_draw = ImageDraw.Draw(bg)

    top = 50

    # 画分区占用列表
    if disks:
        max_len = 990 - (50 + left_padding)  # 进度条长度

        its: List[Tuple[str, sdiskusage | Exception]] = disks.items()  # noqa
        for name, usage in its:
            fail = isinstance(usage, Exception)

            # 进度条背景
            bg_draw.rectangle((50 + left_padding, top, 990, top + 50), GRAY_BG_COLOR)

            # 写盘符
            bg_draw.text((50, top + 25), name, "black", font_45, "lm")

            # 写占用百分比
            bg_draw.text(
                (1150, top + 25),
                f"{usage.percent:.1f}%" if not fail else "未知%",
                "black",
                font_45,
                "rm",
            )

            # 画进度条
            if not fail:
                bg_draw.rectangle(
                    (
                        50 + left_padding,
                        top,
                        50 + left_padding + (max_len * (usage.percent / 100)),
                        top + 50,
                    ),
                    get_usage_color(usage.percent),
                )

            # 写容量信息/报错信息
            bg_draw.text(
                ((max_len / 2) + 50 + left_padding, top + 25),
                (
                    f"{usage.used / 1024 / 1024 / 1024:.2f}G / {usage.total / 1024 / 1024 / 1024:.2f}G"
                    if not fail
                    else str(usage)
                ),
                "black",
                font_40,
                "mm",
            )

            top += 75

    # 写IO统计
    if io_rw:
        if disks:
            # 分隔线 25+10px
            top += 10
            bg_draw.rectangle((50, top - 17, 1150, top - 15), GRAY_BG_COLOR)

        for k, (r, w) in io_rw.items():
            bg_draw.text((50, top + 25), k, "black", font_45, "lm")
            bg_draw.text((1150, top + 25), f"读 {r}/s | 写 {w}/s", "black", font_45, "rm")
            top += 75

    return bg


async def draw_net_io():
    # 获取IO
    io1: Dict[str, snetio] = psutil.net_io_counters(True)
    await asyncio.sleep(1)
    io2: Dict[str, snetio] = psutil.net_io_counters(True)

    ios = {}
    for k, v in io1.items():
        if r := match_list_regexp(config.ps_ignore_nets, k):
            logger.info(f"网卡 {k} 匹配 {r.re.pattern}，忽略")
            continue

        u = io2[k].bytes_sent - v.bytes_sent
        d = io2[k].bytes_recv - v.bytes_recv

        if u == 0 and d == 0 and config.ps_ignore_0b_net:
            logger.info(f"网卡 {k} 上下行0B，忽略")
            continue

        ios[k] = (format_byte_count(u), format_byte_count(d))

    if not ios:
        return None

    font_45 = get_font(45)

    # 计算图片高度并新建图片
    count = len(ios)
    bg = Image.new(
        "RGBA",
        (1200, 100 + (50 * count) + (25 * (count - 1))),  # 上下边距  # 每行磁盘/IO统计  # 间隔
        WHITE_BG_COLOR,
    )
    draw = ImageDraw.Draw(bg)

    # 写字
    top = 50
    for k, (u, d) in ios.items():
        draw.text((50, top + 25), k, "black", font_45, "lm")
        draw.text((1150, top + 25), f"↑ {u}/s | ↓ {d}/s", "black", font_45, "rm")
        top += 75

    return bg


async def draw_footer(img: Image.Image):
    font_22 = get_font(22)
    draw = ImageDraw.Draw(img)
    w, h = img.size
    padding = 15

    draw.text(
        (img.size[0] / 2, h - padding),
        (
            f"NoneBot {nonebot.__version__} × PicStatus {__version__} | "
            f"{platform.python_implementation()} {platform.python_version()} | "
            f"{await get_system_name()} | "
            f"{time.strftime('%Y-%m-%d %H:%M:%S')}"
        ),
        "darkslategray",
        font_22,
        "ms",
    )


async def get_bg(pic: Union[str, bytes, BytesIO] = None) -> Image.Image:
    if config.ps_custom_bg and (not pic):
        pic = random.choice(config.ps_custom_bg)

    if pic:
        try:
            if isinstance(pic, str):
                if pic.startswith("file:///"):
                    return await async_open_img(pic.replace("file:///", "", 1))
                else:
                    pic = await async_request(pic)

            if isinstance(pic, bytes):
                pic = BytesIO(pic)

            return Image.open(pic)
        except:
            logger.exception("下载/打开自定义背景图失败，使用随机背景图")

    try:
        return Image.open(BytesIO(await get_anime_pic()))
    except:
        logger.exception("下载/打开随机背景图失败，使用默认背景图")

    return await async_open_img(DEFAULT_BG_PATH)


async def get_stat_pic(bot: Bot, bg=None):
    img_w = 1300
    img_h = 50  # 这里是上边距，留给下面代码统计图片高度

    # 获取背景及各模块图片
    ret: List[Optional[Image.Image]] = await asyncio.gather(  # noqa
        get_bg(bg),
        draw_header(bot),
        draw_cpu_memory_usage(),
        draw_disk_usage(),
        draw_net_io(),
    )
    bg = ret[0]
    ret = ret[1:]

    # 统计图片高度
    for p in ret:
        if p:
            img_h += p.size[1] + 50

    # 居中裁剪背景
    bg = bg.convert("RGBA")
    bg_w, bg_h = bg.size

    scale = img_w / bg_w
    scaled_h = int(bg_h * scale)

    if scaled_h < img_h:  # 缩放后图片不够高（横屏图）
        # 重算缩放比
        scale = img_h / bg_h
        bg_w = int(bg_w * scale)

        crop_l = round((bg_w / 2) - (img_w / 2))
        bg = bg.resize((bg_w, img_h)).crop((crop_l, 0, crop_l + img_w, img_h))
    else:
        bg_h = scaled_h

        crop_t = round((bg_h / 2) - (img_h / 2))
        bg = bg.resize((img_w, bg_h)).crop((0, crop_t, img_w, crop_t + img_h))

    # 背景高斯模糊
    if config.ps_blur_radius:
        bg = bg.filter(ImageFilter.GaussianBlur(radius=config.ps_blur_radius))

    # 贴一层白色遮罩
    bg.paste(i := Image.new("RGBA", (img_w, img_h), WHITE_MASK_COLOR), mask=i)

    # 将各模块贴上背景
    h_pos = 50
    for p in ret:
        if p:
            bg.paste(p, (50, h_pos), p)
            h_pos += p.size[1] + 50

    # 写footer
    await draw_footer(bg)

    # 尝试解决黑底白底颜色不同问题
    bg = bg.convert("RGB")

    bio = BytesIO()
    bg.save(bio, "png")
    return bio
