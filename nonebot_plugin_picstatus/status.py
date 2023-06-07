import asyncio
import platform
import time
from datetime import datetime
from typing import List, NamedTuple, Optional, Tuple, Union, cast

import anyio
import psutil
from httpx import AsyncClient, ReadTimeout
from nonebot import logger
from nonebot.internal.adapter import Bot
from PIL import Image
from psutil._common import sdiskio, sdiskpart, snetio

from .config import TestSiteCfg, config
from .statistics import bot_connect_time, nonebot_run_time, recv_num, send_num
from .util import format_timedelta, get_bot_avatar, match_list_regexp, process_text_len

try:
    from nonebot.adapters.onebot.v11 import Bot as OBV11Bot
except:
    OBV11Bot = None

try:
    from nonebot.adapters.telegram import Bot as TGBot
except:
    TGBot = None


class HeaderData(NamedTuple):
    avatar: Image.Image
    nick: str
    bot_connected: str
    msg_rec: str
    msg_sent: str
    nb_run: str
    booted: str


class VirtualMemoryStat(NamedTuple):
    percent: float
    used: int
    total: int


class SwapMemoryStat(NamedTuple):
    percent: float
    used: int
    total: int


class CpuFreq(NamedTuple):
    current: Optional[float]
    min: Optional[float]  # noqa: A003
    max: Optional[float]  # noqa: A003


async def get_header_data(bot: Bot) -> HeaderData:
    async def get_bot_status() -> Tuple[str, str, str]:
        nick: Optional[str] = None
        msg_rec: Optional[str] = None
        msg_sent: Optional[str] = None

        if OBV11Bot and isinstance(bot, OBV11Bot):
            bot_stat = (await bot.get_status()).get("stat")
            if bot_stat:
                msg_rec = bot_stat.get("message_received") or bot_stat.get(
                    "MessageReceived",
                )
                msg_sent = bot_stat.get("message_sent") or bot_stat.get("MessageSent")

            if not (config.ps_use_env_nick and config.nickname):
                nick = (await bot.get_login_info())["nickname"]

        if TGBot and isinstance(bot, TGBot):  # noqa: SIM102
            if not (config.ps_use_env_nick and config.nickname):
                nick = (await bot.get_me()).first_name

        if not nick:
            nick = list(config.nickname)[0] if config.nickname else "Bot"
        if msg_rec is None:
            num = recv_num.get(bot.self_id)
            msg_rec = "未知" if num is None else str(num)
        if msg_sent is None:
            num = send_num.get(bot.self_id)
            msg_sent = "未知" if num is None else str(num)

        return nick, msg_rec, msg_sent

    (nick, msg_rec, msg_sent), avatar = await asyncio.gather(
        get_bot_status(),
        get_bot_avatar(bot),
    )

    now_time = datetime.now()
    bot_connected = (
        format_timedelta(now_time - t)
        if (t := bot_connect_time.get(bot.self_id))
        else "未知"
    )
    nb_run = format_timedelta(now_time - nonebot_run_time) if nonebot_run_time else "未知"
    booted = format_timedelta(
        now_time - datetime.fromtimestamp(psutil.boot_time()),
    )

    return HeaderData(
        avatar=avatar,
        nick=nick,
        bot_connected=bot_connected,
        msg_rec=msg_rec,
        msg_sent=msg_sent,
        nb_run=nb_run,
        booted=booted,
    )


class CpuMemoryStat(NamedTuple):
    cpu_percent: float
    cpu_count: int
    cpu_logical_count: int
    cpu_freq: CpuFreq
    ram_stat: VirtualMemoryStat
    swap_stat: SwapMemoryStat


def format_freq_txt(freq: CpuFreq) -> str:
    current, _, max_freq = freq

    if not max_freq:
        if not current:
            return "主频未知"
        return f"当前 {current:.0f}MHz"

    if max_freq == current:
        return f"最大 {max_freq:.0f}MHz"

    return f"{current:.0f}MHz / {max_freq:.0f}MHz"


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


class DiskUsageNormal(NamedTuple):
    name: str
    percent: float
    used: int
    total: int


class DiskUsageWithExc(NamedTuple):
    name: str
    exception: str


DiskUsage = Union[DiskUsageNormal, DiskUsageWithExc]


async def get_disk_usage() -> List[DiskUsage]:
    def get_one(disk: sdiskpart) -> Optional[DiskUsage]:
        mountpoint = disk.mountpoint
        processed_name = process_text_len(mountpoint)

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
                else DiskUsageWithExc(name=processed_name, exception=str(e))
            )

        return DiskUsageNormal(
            name=processed_name,
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


class DiskIO(NamedTuple):
    name: str
    read: int
    write: int


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

        return DiskIO(name=process_text_len(name), read=read, write=write)

    io1 = psutil.disk_io_counters(True)
    await asyncio.sleep(1)
    io2 = psutil.disk_io_counters(True)

    res = [calc_one(name, io1[name], io2[name]) for name in io1 if name in io2]
    res = [x for x in res if x]

    if config.ps_sort_disk_ios:
        res.sort(
            key=lambda x: x.read + x.write,
            reverse=True,
        )

    return res


class DiskStatus(NamedTuple):
    usage: List[DiskUsage]
    io: List[DiskIO]


async def get_disk_status() -> DiskStatus:
    usage, io = await asyncio.gather(get_disk_usage(), get_disk_io())
    return DiskStatus(usage=usage, io=io)


class NetworkIO(NamedTuple):
    name: str
    sent: int
    recv: int


async def get_network_io() -> List[NetworkIO]:
    def calc_one(name: str, past: snetio, now: snetio) -> Optional[NetworkIO]:
        if regex := match_list_regexp(config.ps_ignore_nets, name):
            logger.info(f"网卡IO统计 {name} 匹配 {regex.re.pattern}，忽略")
            return None

        sent = now.bytes_sent - past.bytes_sent
        recv = now.bytes_recv - past.bytes_recv

        if sent == 0 and recv == 0 and config.ps_ignore_0b_net:
            logger.info(f"网卡IO统计 忽略无IO网卡 {name}")
            return None

        return NetworkIO(name=process_text_len(name), sent=sent, recv=recv)

    io1 = psutil.net_io_counters(True)
    await asyncio.sleep(1)
    io2 = psutil.net_io_counters(True)

    res = [calc_one(name, io1[name], io2[name]) for name in io1 if name in io2]
    res = [x for x in res if x]

    if config.ps_sort_nets:
        res.sort(
            key=lambda x: x.sent + x.recv,
            reverse=True,
        )

    return res


class NetworkConnectionOK(NamedTuple):
    name: str
    status: int
    reason: str
    delay: float


class NetworkConnectionError(NamedTuple):
    name: str
    error: str


NetworkConnection = Union[NetworkConnectionOK, NetworkConnectionError]


def format_conn_error(error: Exception) -> str:
    if isinstance(error, ReadTimeout):
        return "超时"
    # if isinstance(v, ClientConnectorError):
    #     tip = f"[{v.os_error.errno}] {v.os_error.strerror}"
    return error.__class__.__name__


async def get_network_connection() -> List[NetworkConnection]:
    async def test_one(site: TestSiteCfg) -> NetworkConnection:
        try:
            async with AsyncClient(
                timeout=config.ps_test_timeout,
                proxies=config.proxy if site.use_proxy else None,
                follow_redirects=True,
            ) as client:
                start = time.time()
                resp = await client.get(site.url)
                delay = (time.time() - start) * 1000

        except Exception as e:
            return NetworkConnectionError(name=site.name, error=format_conn_error(e))

        return NetworkConnectionOK(
            name=site.name,
            status=resp.status_code,
            reason=resp.reason_phrase,
            delay=delay,
        )

    res = await asyncio.gather(*map(test_one, config.ps_test_sites))
    if config.ps_sort_sites:
        res.sort(key=lambda x: x.delay if isinstance(x, NetworkConnectionOK) else -1)

    return res


class NetworkStatus(NamedTuple):
    io: List[NetworkIO]
    connection: List[NetworkConnection]


async def get_network_status() -> NetworkStatus:
    io, connection = await asyncio.gather(get_network_io(), get_network_connection())
    return NetworkStatus(io=io, connection=connection)


class ProcessStatus(NamedTuple):
    name: str
    cpu: float
    mem: int


async def get_process_status() -> List[ProcessStatus]:
    if not config.ps_proc_len:
        return []

    async def parse_one(proc: psutil.Process) -> Optional[ProcessStatus]:
        name = proc.name()
        if regex := match_list_regexp(config.ps_ignore_procs, name):
            logger.info(f"进程 {name} 匹配 {regex.re.pattern}，忽略")
            return None

        proc.cpu_percent()
        await asyncio.sleep(1)
        cpu = proc.cpu_percent()
        cpu = cpu / psutil.cpu_count() if config.ps_proc_cpu_max_100p else cpu

        mem: int = proc.memory_info().rss

        return ProcessStatus(name=process_text_len(name), cpu=cpu, mem=mem)

    def sorter(x: ProcessStatus):
        sort_by = config.ps_proc_sort_by
        if sort_by == "mem":
            return x.mem
        # if sort_by == "cpu":
        return x.cpu

    proc_list = cast(
        List[Union[Optional[ProcessStatus], Exception]],
        await asyncio.gather(
            *(parse_one(proc) for proc in psutil.process_iter()),
            return_exceptions=True,
        ),
    )
    proc_list = [x for x in proc_list if x and (not isinstance(x, Exception))]
    proc_list.sort(key=sorter, reverse=True)
    return proc_list[: config.ps_proc_len]


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
            v = await anyio.Path("/etc/issue").read_text()
        except:
            logger.exception("读取 /etc/issue 文件失败")
            v = f"未知Linux {release}"
        else:
            v = v.replace(r"\n", "").replace(r"\l", "").strip()
        return f"{v} {machine}"

    return f"{system} {release}"
