import asyncio
import platform
import random
import time
from io import BytesIO
from typing import List, Optional, Union

import nonebot
from nonebot import logger
from nonebot.internal.adapter import Bot
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from pil_utils import BuildImage
from pil_utils.fonts import get_proper_font

from .config import config
from .const import DEFAULT_BG_PATH
from .status import (
    CpuMemoryStat,
    DiskStatus,
    DiskUsageWithExc,
    HeaderData,
    NetworkConnectionError,
    NetworkStatus,
    ProcessStatus,
    format_freq_txt,
    get_cpu_memory_usage,
    get_disk_status,
    get_header_data,
    get_network_status,
    get_process_status,
    get_system_name,
)
from .util import (
    async_open_img,
    async_request,
    format_byte_count,
    get_anime_pic,
)
from .version import __version__

GRAY_BG_COLOR: str = "#aaaaaaaa"
WHITE_BG_COLOR = config.ps_bg_color
WHITE_MASK_COLOR = config.ps_mask_color

FONT_PATH = config.ps_font or str(get_proper_font("国").path.resolve())


def get_font(size: int):
    return ImageFont.truetype(FONT_PATH, size)


font_25 = get_font(25)
font_30 = get_font(30)
font_40 = get_font(40)
font_45 = get_font(45)
font_70 = get_font(70)
font_footer = get_font(config.ps_footer_size)


def get_usage_color(usage: float):
    usage = round(usage)
    if usage >= 90:
        return "orangered"
    if usage >= 70:
        return "orange"
    return "lightgreen"


async def draw_header(data: HeaderData) -> Image.Image:
    avatar, nick, bot_connected, msg_rec, msg_sent, nb_run, booted = data

    bg = Image.new("RGBA", (1200, 300), WHITE_BG_COLOR)
    bg_draw = ImageDraw.Draw(bg)

    # 圆形遮罩
    circle_mask = Image.new("RGBA", (250, 250), "#ffffff00")
    ImageDraw.Draw(circle_mask).ellipse((0, 0, 250, 250), fill="black")

    # 利用遮罩裁剪圆形图片
    avatar = avatar.convert("RGBA").resize((250, 250))
    bg.paste(avatar, (25, 25), circle_mask)

    # 标题
    # bg_draw.text((300, 140), nick, "black", font_80, "ld")
    BuildImage(bg).draw_text(
        (300, 25, 1175, 140),
        nick,
        max_fontsize=80,
        halign="left",
        valign="bottom",
        fontname=FONT_PATH,
    )

    # 详细信息
    bg_draw.multiline_text(
        (300, 160),
        (
            f"Bot已连接 {bot_connected} | 收 {msg_rec} | 发 {msg_sent}\n"
            f"NoneBot运行 {nb_run} | 系统运行 {booted}"
        ),
        "black",
        font_30,
    )

    # 标题与详细信息的分隔线
    bg_draw.line((300, 150, 500, 150), GRAY_BG_COLOR, 3)

    return bg


async def draw_cpu_memory_usage(data: CpuMemoryStat) -> Image.Image:
    # 获取占用信息
    cpu_percent, cpu_count, cpu_logical_count, cpu_freq, ram_stat, swap_stat = data

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
    bg_draw.text(
        (200, 470),
        f"{cpu_count}核 {cpu_logical_count}线程",
        "darkslategray",
        font_25,
        "ms",
    )
    bg_draw.text(
        (200, 500),
        format_freq_txt(cpu_freq),
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


async def draw_disk_usage(data: DiskStatus) -> Optional[Image.Image]:
    disk_usage, disk_io = data

    # 列表为空直接返回
    if not (disk_usage and disk_io):
        return None

    # 计算图片高度，创建背景图
    left_padding = max((font_45.getlength(x.name) + 25) for x in disk_usage)
    count = len(disk_usage) + len(disk_io)
    bg = Image.new(
        "RGBA",
        (
            1200,
            100  # 上下边距
            + (50 * count)  # 每行磁盘/IO统计
            + (25 * (count - 1))  # 间隔
            + (10 if disk_usage and disk_io else 0),  # 磁盘统计与IO统计间的间距
        ),
        WHITE_BG_COLOR,
    )
    bg_draw = ImageDraw.Draw(bg)

    top = 50

    # 画分区占用列表
    if disk_usage:
        max_len = 990 - (50 + left_padding)  # 进度条长度

        for usage in disk_usage:
            name = usage.name
            fail = isinstance(usage, DiskUsageWithExc)

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
    if disk_io:
        if disk_usage:
            # 分隔线 25+10px
            top += 10
            bg_draw.rectangle((50, top - 17, 1150, top - 15), GRAY_BG_COLOR)

        for name, read, write in disk_io:
            bg_draw.text((50, top + 25), name, "black", font_45, "lm")
            bg_draw.text(
                (1150, top + 25),
                f"读 {format_byte_count(read)}/s | 写 {format_byte_count(write)}/s",
                "black",
                font_45,
                "rm",
            )
            top += 75

    return bg


async def draw_net_io(data: NetworkStatus) -> Optional[Image.Image]:
    ios, connections = data

    if not (ios and connections):
        return None

    # 计算图片高度并新建图片
    count = len(ios) + len(connections)
    bg = Image.new(
        "RGBA",
        (
            1200,
            100  # 上下边距
            + (50 * count)  # 每行磁盘/IO统计
            + (25 * (count - 1))  # 间隔
            + (10 if ios and connections else 0),  # 网络IO与连通性间距
        ),
        WHITE_BG_COLOR,
    )
    draw = ImageDraw.Draw(bg)

    # 写字
    top = 50
    if ios:
        for name, sent, recv in ios:
            draw.text((50, top + 25), name, "black", font_45, "lm")
            draw.text(
                (1150, top + 25),
                f"↑ {format_byte_count(sent)}/s | ↓ {format_byte_count(recv)}/s",
                "black",
                font_45,
                "rm",
            )
            top += 75

    if connections:
        if ios:
            # 分隔线 25+10px
            top += 10
            draw.rectangle((50, top - 17, 1150, top - 15), GRAY_BG_COLOR)

        for conn in connections:
            name = conn.name
            if isinstance(conn, NetworkConnectionError):
                tip = conn.error
            else:
                _, code, reason, latency = conn
                tip = f"{code} {reason}"
                tip = f"{tip} | {latency:.2f}ms" if code == 200 else tip

            draw.text((50, top + 25), name, "black", font_45, "lm")
            draw.text((1150, top + 25), tip, "black", font_45, "rm")
            top += 75

    return bg


async def draw_process_status(data: List[ProcessStatus]) -> Optional[Image.Image]:
    if not data:
        return None

    # 计算图片高度并新建图片
    count = len(data)
    bg = Image.new(
        "RGBA",
        (1200, 100 + (50 * count) + (25 * (count - 1))),  # 高：上下边距 + 每行 + 间隔
        WHITE_BG_COLOR,
    )
    draw = ImageDraw.Draw(bg)

    offset = 50
    for name, cpu, mem in data:
        draw.text((50, offset + 25), name, "black", font_45, "lm")
        draw.text(
            (1150, offset + 25),
            f"CPU {cpu:.2f}% | MEM {format_byte_count(mem)}",
            "black",
            font_45,
            "rm",
        )
        offset += 75

    return bg


async def draw_footer(img: Image.Image, time_str: str):
    draw = ImageDraw.Draw(img)
    w, h = img.size
    padding = 15

    draw.text(
        (w / 2, h - padding),
        (
            f"NoneBot {nonebot.__version__} × PicStatus {__version__} | "
            f"{platform.python_implementation()} {platform.python_version()} | "
            f"{await get_system_name()} | "
            f"{time_str}"
        ),
        "darkslategray",
        font_footer,
        "ms",
    )


async def get_bg(pic: Optional[Union[bytes, Image.Image]] = None) -> Image.Image:
    if isinstance(pic, Image.Image):
        return pic

    if isinstance(pic, bytes):
        try:
            return Image.open(BytesIO(pic))
        except:
            logger.exception("打开用户自定义背景图失败，弃用")
            pic = None

    if config.ps_custom_bg and (not pic):
        url = random.choice(config.ps_custom_bg)
        try:
            if url.startswith("file:///"):
                return await async_open_img(url[8:])
            return Image.open(await async_request(url))
        except:
            logger.exception("下载/打开自定义背景图失败，使用随机背景图")

    try:
        return Image.open(BytesIO(await get_anime_pic()))
    except:
        logger.exception("下载/打开随机背景图失败，使用默认背景图")

    return await async_open_img(DEFAULT_BG_PATH)


async def get_stat_pic(bot: Bot, bg_arg: Optional[bytes] = None) -> bytes:
    img_w = 1300
    img_h = 50  # 这里是上边距，留给下面代码统计图片高度

    (
        header_data,
        cpu_memory_usage,
        disk_stat,
        net_stat,
        proc_stat,
    ) = await asyncio.gather(
        get_header_data(bot),
        get_cpu_memory_usage(),
        get_disk_status(),
        get_network_status(),
        get_process_status(),
    )
    now_time = time.strftime("%Y-%m-%d %H:%M:%S")

    # 获取背景及各模块图片
    ret = await asyncio.gather(
        get_bg(bg_arg),
        draw_header(header_data),
        draw_cpu_memory_usage(cpu_memory_usage),
        draw_disk_usage(disk_stat),
        draw_net_io(net_stat),
        draw_process_status(proc_stat),
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
    await draw_footer(bg, now_time)

    # 尝试解决黑底白底颜色不同问题
    bg = bg.convert("RGB")

    bio = BytesIO()
    bg.save(bio, "jpeg")
    return bio.getvalue()
