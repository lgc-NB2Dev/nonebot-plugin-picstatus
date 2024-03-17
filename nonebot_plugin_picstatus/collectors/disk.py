from dataclasses import dataclass
from typing import Dict, List, Optional, Union

import psutil
from nonebot import logger
from psutil._common import sdiskio, sdiskpart

from ..config import config
from ..util import match_list_regexp
from . import TimeBasedCounterCollector, collector, periodic_collector


@dataclass
class DiskUsageNormal:
    name: str
    percent: float
    used: int
    total: int


@dataclass
class DiskUsageWithExc:
    name: str
    exception: str


DiskUsageType = Union[DiskUsageNormal, DiskUsageWithExc]


@dataclass
class DiskIO:
    name: str
    read: float
    write: float


@periodic_collector()
async def disk_usage() -> List[DiskUsageType]:
    def get_one(disk: sdiskpart) -> Optional[DiskUsageType]:
        mountpoint = disk.mountpoint

        if match_list_regexp(config.ps_ignore_parts, mountpoint):
            # logger.info(f"空间读取 分区 {mountpoint} 匹配 {regex.re.pattern}，忽略")
            return None

        try:
            usage = psutil.disk_usage(mountpoint)
        except Exception as e:
            logger.exception(f"读取 {mountpoint} 占用失败")
            return (
                None
                if config.ps_ignore_bad_parts
                else DiskUsageWithExc(name=mountpoint, exception=str(e))
            )

        return DiskUsageNormal(
            name=mountpoint,
            percent=usage.percent,
            used=usage.used,
            total=usage.total,
        )

    usage = [x for x in map(get_one, psutil.disk_partitions()) if x]
    if config.ps_sort_parts:
        usage.sort(
            key=lambda x: x.percent if isinstance(x, DiskUsageNormal) else -1,
            reverse=not config.ps_sort_parts_reverse,
        )

    return usage


@collector("disk_io")
class DiskIOCollector(TimeBasedCounterCollector[Dict[str, sdiskio], List[DiskIO]]):
    async def _calc(
        self,
        past: Dict[str, sdiskio],
        now: Dict[str, sdiskio],
        time_passed: float,
    ) -> List[DiskIO]:
        def calc_one(name: str, past_it: sdiskio, now_it: sdiskio) -> Optional[DiskIO]:
            if match_list_regexp(config.ps_ignore_disk_ios, name):
                # logger.info(f"IO统计 磁盘 {name} 匹配 {regex.re.pattern}，忽略")
                return None

            read = (now_it.read_bytes - past_it.read_bytes) / time_passed
            write = (now_it.write_bytes - past_it.write_bytes) / time_passed

            if read == 0 and write == 0 and config.ps_ignore_no_io_disk:
                # logger.info(f"IO统计 忽略无IO磁盘 {name}")
                return None

            return DiskIO(name=name, read=read, write=write)

        res = [calc_one(name, past[name], now[name]) for name in past if name in now]
        res = [x for x in res if x]
        if config.ps_sort_disk_ios:
            res.sort(key=lambda x: x.read + x.write, reverse=True)
        return res

    async def _get_obj(self) -> Dict[str, sdiskio]:
        return psutil.disk_io_counters(perdisk=True)
