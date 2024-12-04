import asyncio as aio
import mimetypes
import random
from collections.abc import Awaitable
from typing import TYPE_CHECKING, Callable, NamedTuple, Optional, TypeVar

import anyio
from httpx import AsyncClient, Response
from nonebot import logger

from .config import DEFAULT_BG_PATH, config

if TYPE_CHECKING:
    from pathlib import Path


class BgData(NamedTuple):
    data: bytes
    mime: str


BGProviderType = Callable[[], Awaitable[BgData]]
TBP = TypeVar("TBP", bound=BGProviderType)

registered_bg_providers: dict[str, BGProviderType] = {}


def get_bg_files() -> list["Path"]:
    if not config.ps_bg_local_path.exists():
        logger.warning("Custom background path does not exist, fallback to default")
        return [DEFAULT_BG_PATH]
    if config.ps_bg_local_path.is_file():
        return [config.ps_bg_local_path]

    files = [x for x in config.ps_bg_local_path.glob("*") if x.is_file()]
    if not files:
        logger.warning("Custom background dir has no file in it, fallback to default")
        return [DEFAULT_BG_PATH]
    return files


BG_FILES = get_bg_files()


def bg_provider(name: Optional[str] = None):
    def deco(func: TBP) -> TBP:
        provider_name = name or func.__name__
        if provider_name in registered_bg_providers:
            raise ValueError(f"Duplicate bg provider name `{provider_name}`")
        registered_bg_providers[provider_name] = func
        return func

    return deco


def resp_to_bg_data(resp: Response):
    return BgData(
        resp.content,
        (resp.headers.get("Content-Type") or "application/octet-stream"),
    )


@bg_provider()
async def loli():
    async with AsyncClient(
        follow_redirects=True,
        proxies=config.proxy,
        timeout=config.ps_req_timeout,
    ) as cli:
        return resp_to_bg_data(
            (await cli.get("https://www.loliapi.com/acg/pe/")).raise_for_status(),
        )


@bg_provider()
async def lolicon():
    async with AsyncClient(
        follow_redirects=True,
        proxies=config.proxy,
        timeout=config.ps_req_timeout,
    ) as cli:
        resp = await cli.get(
            "https://api.lolicon.app/setu/v2",
            params={
                "r18": config.ps_bg_lolicon_r18_type,
                "proxy": "false",
                "excludeAI": "true",
            },
        )
        url = resp.raise_for_status().json()["data"][0]["urls"]["original"]
        resp = await cli.get(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/119.0.0.0 "
                    "Safari/537.36"
                ),
                "Referer": "https://www.pixiv.net/",
            },
        )
        return resp_to_bg_data(resp)


@bg_provider()
async def local():
    file = random.choice(BG_FILES)
    logger.debug(f"Choice background file `{file}`")
    return BgData(
        await anyio.Path(file).read_bytes(),
        mimetypes.guess_type(file)[0] or "application/octet-stream",
    )


@bg_provider()
async def none():
    return BgData(b"", "application/octet-stream")


async def fetch_bg() -> BgData:
    if config.ps_bg_provider in registered_bg_providers:
        try:
            return await registered_bg_providers[config.ps_bg_provider]()
        except Exception:
            logger.exception("Error when getting background, fallback to local")
    else:
        logger.warning(
            f"Unknown background provider `{config.ps_bg_provider}`, fallback to local",
        )
    return await local()


class BgPreloader:
    def __init__(self, preload_count: int):
        if preload_count < 1:
            raise ValueError("preload_count must be greater than 0")
        self.preload_count = preload_count
        self.backgrounds: list[BgData] = []
        self.tasks: list[aio.Task[None]] = []
        self.task_signal: Optional[aio.Future[None]] = None
        self.signal_wait_lock = aio.Lock()

    def _get_signal(self) -> aio.Future[None]:
        if (not self.task_signal) or self.task_signal.done():
            self.task_signal = aio.Future()
        return self.task_signal

    def _wait_signal(self):
        async def inner():
            async with self.signal_wait_lock:
                await self._get_signal()

        return aio.wait_for(inner(), timeout=15)

    def create_preload_task(self):
        async def task_func():
            logger.debug("Started a preload background task")
            try:
                bg = await fetch_bg()
            except Exception as e:
                # fetch_bg has fallback so it should ensure we can get a bg
                # if error occurred this should be an unexpected error
                # need to let this error raise
                logger.opt(exception=e).debug("Exception when preloading")
                if not (s := self._get_signal()).done():
                    s.set_exception(e)
            else:
                logger.debug("A preload task done")
                self.backgrounds.append(bg)
                if not (s := self._get_signal()).done():
                    s.set_result(None)
            finally:
                self.tasks.remove(task)

        task = aio.create_task(task_func())
        self.tasks.append(task)

    def start_preload(self, create_when_full: bool = False):
        task_count = self.preload_count - len(self.backgrounds) - len(self.tasks)
        if task_count <= 0:
            if not create_when_full:
                return
            task_count = 1
        logger.debug(f"Will preload {task_count} backgrounds")
        for _ in range(task_count):
            self.create_preload_task()

    async def get(self) -> BgData:
        if not self.backgrounds:
            self.start_preload(create_when_full=True)
            if self.tasks:
                await self._wait_signal()
            if not self.backgrounds:
                raise RuntimeError("Failed to wait background")
        bg = self.backgrounds.pop(0)
        self.start_preload()
        return bg


bg_preloader = BgPreloader(config.ps_bg_preload_count)
