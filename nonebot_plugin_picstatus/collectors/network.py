import asyncio
import time
from dataclasses import dataclass
from typing import TypeAlias

import psutil
from httpx import AsyncClient, ReadTimeout
from psutil._common import snetio

from ..config import TestSiteCfg, config
from ..util import match_list_regexp
from . import (
    BaseTimeBasedCounterCollector,
    NormalTimeBasedCounterCollector,
    PeriodicTimeBasedCounterCollector,
    collector,
    normal_collector,
)


@dataclass
class NetworkIO:
    name: str
    sent: float
    recv: float


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


NetworkConnectionType: TypeAlias = NetworkConnectionOK | NetworkConnectionError


class BaseNetworkIOCollector(
    BaseTimeBasedCounterCollector[dict[str, snetio], list[NetworkIO]],
):
    async def _calc(
        self,
        past: dict[str, snetio],
        now: dict[str, snetio],
        time_passed: float,
    ) -> list[NetworkIO]:
        def calc_one(name: str, past_it: snetio, now_it: snetio) -> NetworkIO | None:
            if match_list_regexp(config.ps_ignore_nets, name):
                # logger.info(f"网卡IO统计 {name} 匹配 {regex.re.pattern}，忽略")
                return None

            sent = (now_it.bytes_sent - past_it.bytes_sent) / time_passed
            recv = (now_it.bytes_recv - past_it.bytes_recv) / time_passed

            if sent == 0 and recv == 0 and config.ps_ignore_0b_net:
                # logger.info(f"网卡IO统计 忽略无IO网卡 {name}")
                return None

            return NetworkIO(name=name, sent=sent, recv=recv)

        res = [calc_one(name, past[name], now[name]) for name in past if name in now]
        res = [x for x in res if x]
        if config.ps_sort_nets:
            res.sort(key=lambda x: x.sent + x.recv, reverse=True)
        return res

    async def _get_obj(self) -> dict[str, snetio]:
        return psutil.net_io_counters(pernic=True)


@collector("network_io")
class NormalDiskIOCollector(
    BaseNetworkIOCollector,
    NormalTimeBasedCounterCollector[dict[str, snetio], list[NetworkIO]],
): ...


@collector("network_io_periodic")
class PeriodicDiskIOCollector(
    BaseNetworkIOCollector,
    PeriodicTimeBasedCounterCollector[dict[str, snetio], list[NetworkIO]],
): ...


@normal_collector()
async def network_connection() -> list[NetworkConnectionType]:
    def format_conn_error(error: Exception) -> str:
        if isinstance(error, ReadTimeout):
            return "超时"
        return error.__class__.__name__

    async def test_one(site: TestSiteCfg) -> NetworkConnectionType:
        try:
            async with AsyncClient(
                timeout=config.ps_test_timeout,
                proxy=config.proxy if site.use_proxy else None,
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
