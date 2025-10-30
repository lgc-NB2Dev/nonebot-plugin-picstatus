import asyncio as aio
import mimetypes
import random
import sys
import time
from abc import ABC, abstractmethod
from collections.abc import AsyncIterable, Callable
from math import floor
from pathlib import Path
from typing import Generic, NamedTuple, ParamSpec, TypeAlias, TypedDict, TypeVar
from typing_extensions import override

from cookit.common import race
from cookit.loguru import warning_suppress
from httpx import AsyncClient, Response
from nonebot import get_driver, logger

from .config import BG_PRELOAD_CACHE_DIR, DEFAULT_BG_PATH, config

if sys.version_info >= (3, 11):
    from asyncio.taskgroups import TaskGroup
else:
    from taskgroup import TaskGroup


class BgBytesData(NamedTuple):
    data: bytes | None
    mime: str


class BgFileData(NamedTuple):
    path: Path | None
    mime: str


BgData: TypeAlias = BgBytesData | BgFileData

BGProviderType = Callable[[int], AsyncIterable[BgData]]
T = TypeVar("T")
TBP = TypeVar("TBP", bound=BGProviderType)
P = ParamSpec("P")

DEFAULT_MIME = "application/octet-stream"

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


def refresh_bg_files():
    global BG_FILES
    BG_FILES = get_bg_files()


def bg_provider(name: str | None = None):
    def deco(func: TBP) -> TBP:
        provider_name = name or func.__name__
        if provider_name in registered_bg_providers:
            raise ValueError(f"Duplicate bg provider name `{provider_name}`")
        registered_bg_providers[provider_name] = func
        return func

    return deco


def iter_batch_sizes(size: int, max_size: int):
    if size <= max_size:
        yield size
    else:
        full_sizes = floor(max_size / size)
        for _ in range(full_sizes):
            yield max_size
        if rest_count := full_sizes * max_size:
            yield rest_count


def resp_to_bg_data(resp: Response):
    return BgBytesData(
        resp.content,
        (resp.headers.get("Content-Type") or DEFAULT_MIME),
    )


class CoIterator(ABC, Generic[T]):
    def __init__(self):
        self.queue = aio.Queue[T | None]()

    @abstractmethod
    async def run_tasks(self): ...

    async def run(self):
        await self.run_tasks()
        await self.queue.put(None)

    async def __aiter__(self):
        async with TaskGroup() as t:
            t.create_task(self.run())
            while (x := await self.queue.get()) is not None:
                yield x


@bg_provider("loli")
class LoliBGProvider(CoIterator[BgData]):
    def __init__(self, num: int):
        super().__init__()
        self.num = num
        self.sem = aio.Semaphore(4)

    async def task_piece(self, cli: AsyncClient):
        async with self.sem:
            with warning_suppress("Failed to fetch image"):
                x = resp_to_bg_data(
                    (
                        await cli.get("https://www.loliapi.com/acg/pe/")
                    ).raise_for_status(),
                )
                await self.queue.put(x)

    @override
    async def run_tasks(self):
        async with AsyncClient(
            follow_redirects=True,
            proxy=config.proxy,
            timeout=config.ps_req_timeout,
        ) as cli:
            await aio.gather(*(self.task_piece(cli) for _ in range(self.num)))


class LoliconRespDataUrls(TypedDict):
    original: str


class LoliconRespData(TypedDict):
    urls: LoliconRespDataUrls


class LoliconResp(TypedDict):
    data: list[LoliconRespData]


@bg_provider("lolicon")
class LoliconBGProvider(CoIterator[BgData]):
    def __init__(self, num: int):
        super().__init__()
        self.num = num
        self.sem = aio.Semaphore(4)
        self.url_queue = aio.Queue[str | None]()

    async def do_fetch_urls_piece(self, num: int, cli: AsyncClient):
        with warning_suppress("Failed to fetch urls"):
            resp = await cli.get(
                "https://api.lolicon.app/setu/v2",
                params={
                    "num": num,
                    "r18": config.ps_bg_lolicon_r18_type,
                    "proxy": "false",
                    "excludeAI": "true",
                },
            )
            data: LoliconResp = resp.raise_for_status().json()
            for x in data["data"]:
                await self.url_queue.put(x["urls"]["original"])

    async def fetch_urls_task_f(self):
        async with AsyncClient(
            follow_redirects=True,
            proxy=config.proxy,
            timeout=config.ps_req_timeout,
        ) as cli:
            for x in iter_batch_sizes(self.num, 20):
                await self.do_fetch_urls_piece(x, cli)
        await self.url_queue.put(None)

    async def fetch_image(self, url: str, cli: AsyncClient):
        async with self.sem:
            with warning_suppress("Failed to fetch image"):
                bg = resp_to_bg_data((await cli.get(url)).raise_for_status())
                await self.queue.put(bg)

    @override
    async def run_tasks(self):
        pixiv_client = AsyncClient(
            follow_redirects=True,
            proxy=config.proxy,
            timeout=config.ps_req_timeout,
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
        async with TaskGroup() as t, pixiv_client:
            t.create_task(self.fetch_urls_task_f())
            while (x := await self.url_queue.get()) is not None:
                t.create_task(self.fetch_image(x, pixiv_client))


@bg_provider()
async def local(num: int):
    files = random.sample(BG_FILES, num)
    # logger.debug(f"Chosen background `{files}`")
    for x in files:
        yield BgFileData(
            x,
            mimetypes.guess_type(x)[0] or DEFAULT_MIME,
        )


def create_none_bg():
    return BgBytesData(None, DEFAULT_MIME)


@bg_provider()
async def none(num: int):
    for _ in range(num):
        yield create_none_bg()


async def fetch_bg(num: int) -> AsyncIterable[BgData]:
    if config.ps_bg_provider not in registered_bg_providers:
        logger.warning(
            f"Unknown background provider `{config.ps_bg_provider}`, fallback to local",
        )
        async for x in local(num):
            yield x
        return

    # at least we should return one image (x)
    # has_img = False
    try:
        provider = registered_bg_providers[config.ps_bg_provider]
        async for x in provider(num):
            # has_img = True
            yield x
    except Exception:
        logger.exception(
            "Error when getting background, fallback to get one local bg",
        )
        async for x in local(1):
            yield x
    # else:
    #     if has_img:
    #         return
    #     logger.warning(
    #         "Background provider returned empty iterator, fallback to get one local bg",
    #     )
    #     async for x in local(1):
    #         yield x


def cache_bg(bg: BgBytesData):
    if not bg.data:
        return BgFileData(None, bg.mime)
    BG_PRELOAD_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = BG_PRELOAD_CACHE_DIR / f"{time.time_ns()}.{bg.mime.split('/')[-1]}"
    path.write_bytes(bg.data)
    return BgFileData(path, bg.mime)


def read_cached_bg_file(bg: BgFileData) -> BgBytesData | None:
    if not bg.path:
        return BgBytesData(None, bg.mime)
    with warning_suppress("Failed to read cached file"):
        data = bg.path.read_bytes()
        if bg.path.is_relative_to(BG_PRELOAD_CACHE_DIR):
            with warning_suppress("Failed to unlink cached file"):
                bg.path.unlink()
        return BgBytesData(data, bg.mime)
    return None


async def get_one_fallback() -> BgBytesData:
    with warning_suppress("Failed to get local bg file, fallback to none"):
        async for x in local(1):
            if bg := read_cached_bg_file(x):
                return bg
    logger.warning("Failed to read local bg file, fallback to none")
    return create_none_bg()


class BgPreloader:
    def __init__(self, preload_count: int):
        # if preload_count < 1:
        #     raise ValueError("preload_count must be greater than or equals 1")
        self.preload_count = preload_count
        self.background_queue = aio.Queue[BgData]()
        self.current_load_task_main: aio.Task | None = None
        self.consumed_in_loading: bool = False
        self.image_got_signal = aio.Event()
        self.fire_tasks: set[aio.Task] = set()

    # we allow fetch_bg return less image than we require
    async def preload_task(
        self,
        count: int,
        fire: bool = False,
        fire_done_signal: aio.Event | None = None,
    ):
        logger.debug(f"Preload task started, will preload {count} images, {fire=}")
        try:
            async for x in fetch_bg(count):
                logger.debug("Got one image")
                if self.preload_count > 0 or (
                    fire_done_signal and fire_done_signal.is_set()
                ):
                    x = cache_bg(x) if isinstance(x, BgBytesData) else x
                await self.background_queue.put(x)
                self.image_got_signal.set()
                self.image_got_signal.clear()
        except Exception:
            logger.exception("Unexpected error occurred in preload task")
        else:
            logger.debug("Preload task finished")

        if fire:
            return
        if (
            self.consumed_in_loading
            or self.background_queue.qsize() < self.preload_count
        ):
            self.consumed_in_loading = False
            self.start_preload()
        else:
            self.current_load_task_main = None

    def start_preload(self, force: bool = False):
        count = self.preload_count - self.background_queue.qsize()
        if count <= 0 and not force:
            logger.debug(
                "Current background queue size meets preload count, skip preload",
            )
            return
        task = aio.create_task(self.preload_task(count))
        self.current_load_task_main = task

    def set_defer_preload(self):
        if self.current_load_task_main:
            logger.debug("Main preload task already running, set flag")
            self.consumed_in_loading = True
        else:
            self.start_preload()

    async def _get_on_fire(self) -> BgBytesData:
        task_done_signal = aio.Event()
        fire_task = aio.create_task(
            self.preload_task(1, fire=True, fire_done_signal=task_done_signal),
        )
        fire_task.add_done_callback(lambda _: task_done_signal.set())
        fire_task.add_done_callback(lambda _: self.fire_tasks.discard(fire_task))
        self.fire_tasks.add(fire_task)
        try:
            await race(
                # self.image_got_signal.wait(),  # lazy to handle this racing condition now
                task_done_signal.wait(),
                aio.sleep(15),
            )
        finally:
            task_done_signal.set()
            # fire_task.cancel()  # should we cancel here? i'm letting it cache to queue

        if not self.background_queue.empty():
            bg = await self.background_queue.get()
            self.set_defer_preload()
            if (not isinstance(bg, BgFileData)) or (bg := read_cached_bg_file(bg)):
                return bg

        logger.error("Unable to get an background image, falling back to local")
        return await get_one_fallback()

    async def get(self) -> BgBytesData:
        self.set_defer_preload()

        while not self.background_queue.empty():
            bg = await self.background_queue.get()
            self.set_defer_preload()
            if (not isinstance(bg, BgFileData)) or (bg := read_cached_bg_file(bg)):
                return bg

        # normally all items in queue should be valid
        # if they not, we should fetch
        return await self._get_on_fire()


bg_preloader = BgPreloader(config.ps_bg_preload_count)

driver = get_driver()


@driver.on_shutdown
async def _():
    for t in bg_preloader.fire_tasks:
        t.cancel()
