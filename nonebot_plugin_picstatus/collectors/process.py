import asyncio
from dataclasses import dataclass
from typing import cast

import psutil

from ..config import config
from ..util import match_list_regexp
from . import normal_collector, periodic_collector


@dataclass
class ProcessStatus:
    name: str
    cpu: float
    mem: int


async def get_process_status() -> list[ProcessStatus]:
    if not config.ps_proc_len:
        return []

    async def parse_one(proc: psutil.Process) -> ProcessStatus | None:
        name = proc.name()
        if match_list_regexp(config.ps_ignore_procs, name):
            # logger.info(f"进程 {name} 匹配 {regex.re.pattern}，忽略")
            return None

        # proc.cpu_percent()
        # await asyncio.sleep(1)
        cpu_count = psutil.cpu_count()
        with proc.oneshot():
            cpu = proc.cpu_percent()
            cpu = (
                (cpu / cpu_count) if config.ps_proc_cpu_max_100p and cpu_count else cpu
            )
            mem: int = proc.memory_info().rss

        return ProcessStatus(name=name, cpu=cpu, mem=mem)

    def sorter(x: ProcessStatus):
        sort_by = config.ps_proc_sort_by
        if sort_by == "mem":
            return x.mem
        # if sort_by == "cpu":
        return x.cpu

    proc_list = cast(
        "list[ProcessStatus | None | Exception]",
        await asyncio.gather(
            *(parse_one(proc) for proc in psutil.process_iter()),
            return_exceptions=True,
        ),
    )
    proc_list = [x for x in proc_list if x and (not isinstance(x, Exception))]
    proc_list.sort(key=sorter, reverse=True)
    return proc_list[: config.ps_proc_len]


normal_collector("process_status")(get_process_status)
periodic_collector("process_status_periodic")(get_process_status)
