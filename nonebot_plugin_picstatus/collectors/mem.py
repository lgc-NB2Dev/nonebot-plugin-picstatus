from dataclasses import dataclass

import psutil

from . import normal_collector, periodic_collector


@dataclass
class MemoryStat:
    percent: float
    used: int
    total: int


async def get_memory_stat() -> MemoryStat:
    mem = psutil.virtual_memory()
    return MemoryStat(percent=mem.percent, used=mem.used, total=mem.total)


normal_collector("memory_stat")(get_memory_stat)
periodic_collector("memory_stat_periodic")(get_memory_stat)


async def get_swap_stat() -> MemoryStat:
    swap = psutil.swap_memory()
    return MemoryStat(percent=swap.percent, used=swap.used, total=swap.total)


normal_collector("swap_stat")(get_swap_stat)
periodic_collector("swap_stat_periodic")(get_swap_stat)
