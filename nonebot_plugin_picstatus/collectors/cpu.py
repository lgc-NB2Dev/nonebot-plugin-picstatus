from dataclasses import dataclass
from typing import Optional, cast

import psutil
from cpuinfo import get_cpu_info
from nonebot import logger

from . import first_time_collector, periodic_collector


@dataclass
class CpuFreq:
    current: Optional[float]
    min: Optional[float]  # noqa: A003
    max: Optional[float]  # noqa: A003


@first_time_collector()
async def cpu_brand() -> str:
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


@first_time_collector()
async def cpu_count_logical() -> int:
    return psutil.cpu_count()


@first_time_collector()
async def cpu_count() -> int:
    return psutil.cpu_count(logical=False)


@periodic_collector()
async def cpu_percent() -> float:
    return psutil.cpu_percent()


@periodic_collector()
async def cpu_freq() -> CpuFreq:
    cpu_freq = psutil.cpu_freq()
    return CpuFreq(
        current=getattr(cpu_freq, "current", None),
        min=getattr(cpu_freq, "min", None),
        max=getattr(cpu_freq, "max", None),
    )
