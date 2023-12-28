import asyncio
from dataclasses import dataclass
from typing import List, Optional, Union

import psutil
from nonebot import logger
from psutil._common import sdiskio, sdiskpart

from ..config import config
from ..render import ENVIRONMENT
from ..util import match_list_regexp
from . import register_component


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
    read: int
    write: int


@dataclass
class DiskStatus:
    usage: List[DiskUsageType]
    io: List[DiskIO]


async def get_disk_usage() -> List[DiskUsageType]:
    def get_one(disk: sdiskpart) -> Optional[DiskUsageType]:
        mountpoint = disk.mountpoint

        if regex := match_list_regexp(config.ps_ignore_parts, mountpoint):
            logger.info(f"空间读取 分区 {mountpoint} 匹配 {regex.re.pattern}，忽略")
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


async def get_disk_io() -> List[DiskIO]:
    def calc_one(name: str, past: sdiskio, now: sdiskio) -> Optional[DiskIO]:
        if regex := match_list_regexp(config.ps_ignore_disk_ios, name):
            logger.info(f"IO统计 磁盘 {name} 匹配 {regex.re.pattern}，忽略")
            return None

        read = now.read_bytes - past.read_bytes
        write = now.write_bytes - past.write_bytes

        if read == 0 and write == 0 and config.ps_ignore_no_io_disk:
            logger.info(f"IO统计 忽略无IO磁盘 {name}")
            return None

        return DiskIO(name=name, read=read, write=write)

    io1 = psutil.disk_io_counters(perdisk=True)
    await asyncio.sleep(1)
    io2 = psutil.disk_io_counters(perdisk=True)

    res = [calc_one(name, io1[name], io2[name]) for name in io1 if name in io2]
    res = [x for x in res if x]

    if config.ps_sort_disk_ios:
        res.sort(
            key=lambda x: x.read + x.write,
            reverse=True,
        )

    return res


async def get_disk_status() -> DiskStatus:
    usage, io = await asyncio.gather(get_disk_usage(), get_disk_io())
    return DiskStatus(usage=usage, io=io)


@register_component
async def disk():
    return await ENVIRONMENT.get_template("disk.html.jinja").render_async(
        data=await get_disk_status(),
    )
