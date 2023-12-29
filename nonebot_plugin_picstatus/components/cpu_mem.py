import asyncio
from dataclasses import dataclass
from functools import partial
from typing import List, Optional, cast

import psutil
from cpuinfo import get_cpu_info
from nonebot import logger

from ..render import ENVIRONMENT
from ..util import auto_convert_unit
from . import register_component


@dataclass
class VirtualMemoryStat:
    percent: float
    used: int
    total: int


@dataclass
class SwapMemoryStat:
    percent: float
    used: int
    total: int


@dataclass
class CpuFreq:
    current: Optional[float]
    min: Optional[float]  # noqa: A003
    max: Optional[float]  # noqa: A003


@dataclass
class CpuMemoryStat:
    cpu_percent: float
    cpu_count: int
    cpu_logical_count: int
    cpu_brand: Optional[str]
    cpu_freq: CpuFreq
    ram_stat: VirtualMemoryStat
    swap_stat: SwapMemoryStat


@dataclass
class DonutData:
    percent: Optional[float]
    title: str
    caption: str


def get_cpu_brand() -> str:
    try:
        brand = (
            cast(str, get_cpu_info().get("brand_raw", ""))
            .split("@", maxsplit=1)[0]
            .strip()
        )
        if brand.lower().endswith(("cpu", "processor")):
            brand = brand.rsplit(maxsplit=1)[0].strip()
    except Exception:
        logger.exception("Error when getting CPU brand")
        return "未知型号"
    else:
        return brand


cpu_brand = get_cpu_brand()


def format_freq_txt(freq: CpuFreq) -> str:
    cu = partial(auto_convert_unit, suffix="Hz", multiplier=1000, unit_index=2)
    if not freq.current:
        return "主频未知"
    if not freq.max:
        return cu(freq.current)
    if freq.max == freq.current:
        return cu(freq.max)
    return f"{cu(freq.current)} / {cu(freq.max)}"


async def get_cpu_memory_usage() -> CpuMemoryStat:
    psutil.cpu_percent()
    await asyncio.sleep(0.1)
    cpu_percent = psutil.cpu_percent()

    cpu_count = psutil.cpu_count(logical=False)
    cpu_count_logical = psutil.cpu_count()
    cpu_freq = psutil.cpu_freq()
    ram_stat = psutil.virtual_memory()
    swap_stat = psutil.swap_memory()

    return CpuMemoryStat(
        cpu_percent=cpu_percent,
        cpu_count=cpu_count,
        cpu_logical_count=cpu_count_logical,
        cpu_brand=cpu_brand,
        cpu_freq=CpuFreq(
            current=getattr(cpu_freq, "current", None),
            min=getattr(cpu_freq, "min", None),
            max=getattr(cpu_freq, "max", None),
        ),
        ram_stat=VirtualMemoryStat(
            percent=ram_stat.percent,
            used=ram_stat.used,
            total=ram_stat.total,
        ),
        swap_stat=SwapMemoryStat(
            percent=swap_stat.percent,
            used=swap_stat.used,
            total=swap_stat.total,
        ),
    )


def to_donut_data(data: CpuMemoryStat) -> List[DonutData]:
    return [
        DonutData(
            percent=data.cpu_percent,
            title="CPU",
            caption=(
                f"{data.cpu_count}核 {data.cpu_logical_count}线程 {format_freq_txt(data.cpu_freq)}\n"
                f"{data.cpu_brand}"
            ),
        ),
        DonutData(
            percent=data.ram_stat.percent,
            title="RAM",
            caption=f"{auto_convert_unit(data.ram_stat.used)} / {auto_convert_unit(data.ram_stat.total)}",
        ),
        DonutData(
            percent=data.swap_stat.percent if data.swap_stat.total > 0 else None,
            title="SWAP",
            caption=(
                f"{auto_convert_unit(data.swap_stat.used)} / {auto_convert_unit(data.swap_stat.total)}"
                if data.swap_stat.total > 0
                else "??.??B / ??.??B"
            ),
        ),
    ]


@register_component
async def cpu_mem():
    return await ENVIRONMENT.get_template("cpu_mem.html.jinja").render_async(
        data=to_donut_data(await get_cpu_memory_usage()),
    )
