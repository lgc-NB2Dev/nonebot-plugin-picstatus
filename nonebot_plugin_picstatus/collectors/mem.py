from dataclasses import dataclass

import psutil

from . import periodic_collector


@dataclass
class MemoryStat:
    percent: float
    used: int
    total: int


@periodic_collector()
async def memory_stat() -> MemoryStat:
    mem = psutil.virtual_memory()
    return MemoryStat(percent=mem.percent, used=mem.used, total=mem.total)


@periodic_collector()
async def swap_stat() -> MemoryStat:
    swap = psutil.swap_memory()
    return MemoryStat(percent=swap.percent, used=swap.used, total=swap.total)
