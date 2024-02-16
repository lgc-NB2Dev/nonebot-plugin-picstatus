import asyncio
import time
from dataclasses import dataclass
from typing import List, Optional, Union

import psutil
from httpx import AsyncClient, ReadTimeout
from nonebot import logger
from psutil._common import snetio

from ..config import TestSiteCfg, config
from ..render import ENVIRONMENT
from ..util import match_list_regexp
from . import register_component


@dataclass
class NetworkIO:
    name: str
    sent: int
    recv: int


@dataclass
class NetworkConnectionOK:
    name: str
    status: int
    reason: str
    delay: float


@dataclass
class NetworkConnectionError:
    name: str
    error: str


NetworkConnectionType = Union[NetworkConnectionOK, NetworkConnectionError]


@dataclass
class NetworkStatus:
    io: List[NetworkIO]
    connection: List[NetworkConnectionType]


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

        return NetworkIO(name=name, sent=sent, recv=recv)

    io1 = psutil.net_io_counters(pernic=True)
    await asyncio.sleep(1)
    io2 = psutil.net_io_counters(pernic=True)

    res = [calc_one(name, io1[name], io2[name]) for name in io1 if name in io2]
    res = [x for x in res if x]

    if config.ps_sort_nets:
        res.sort(
            key=lambda x: x.sent + x.recv,
            reverse=True,
        )

    return res


def format_conn_error(error: Exception) -> str:
    if isinstance(error, ReadTimeout):
        return "超时"
    # if isinstance(v, ClientConnectorError):
    #     tip = f"[{v.os_error.errno}] {v.os_error.strerror}"
    return error.__class__.__name__


async def get_network_connection() -> List[NetworkConnectionType]:
    async def test_one(site: TestSiteCfg) -> NetworkConnectionType:
        try:
            async with AsyncClient(
                timeout=config.ps_test_timeout,
                proxies=config.proxy if site.use_proxy else None,
                follow_redirects=True,
            ) as client:
                start = time.time()
                resp = await client.get(str(site.url))
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


async def get_network_status() -> NetworkStatus:
    io, connection = await asyncio.gather(get_network_io(), get_network_connection())
    return NetworkStatus(io=io, connection=connection)


@register_component
async def network():
    return await ENVIRONMENT.get_template("network.html.jinja").render_async(
        data=await get_network_status(),
    )
