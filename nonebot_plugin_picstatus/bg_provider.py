import asyncio as aio
import mimetypes
import random
import sys
import time
from abc import ABC, abstractmethod
from collections.abc import AsyncIterable, Callable
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Generic,
    NamedTuple,
    ParamSpec,
    TypeAlias,
    TypedDict,
    TypeVar,
)
from typing_extensions import override

from cookit.loguru import log_exception_warning, warning_suppress
from nonebot import get_driver, logger

from .config import BG_PRELOAD_CACHE_DIR, DEFAULT_BG_PATH, config
from .util import make_http_client

if TYPE_CHECKING:
    from httpx import AsyncClient, Response

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


class RegisteredBGProvider(NamedTuple):
    factory: BGProviderType
    no_preload: bool = False


T = TypeVar("T")
TBP = TypeVar("TBP", bound=BGProviderType)
P = ParamSpec("P")

DEFAULT_MIME = "application/octet-stream"

registered_bg_providers: dict[str, RegisteredBGProvider] = {}


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


def bg_provider(name: str | None = None, *, no_preload: bool = False):
    def deco(func: TBP) -> TBP:
        provider_name = name or func.__name__
        if provider_name in registered_bg_providers:
            raise ValueError(f"Duplicate bg provider name `{provider_name}`")
        registered_bg_providers[provider_name] = RegisteredBGProvider(func, no_preload)
        return func

    return deco


def iter_batch_sizes(size: int, max_size: int):
    if size <= 0 or max_size <= 0:
        raise ValueError("Batch size and provider limit must be positive")
    full_batches, remainder = divmod(size, max_size)
    yield from (max_size for _ in range(full_batches))
    if remainder:
        yield remainder


def resp_to_bg_data(resp: "Response"):
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


class BaseUrlBGProvider(CoIterator[BgData]):
    def __init__(self, num: int, url: str, concurrency: int = 4):
        super().__init__()
        self.num = num
        self.url = url
        self.sem = aio.Semaphore(concurrency)

    async def task_piece(self, cli: "AsyncClient"):
        async with self.sem:
            with warning_suppress("Failed to fetch image"):
                x = resp_to_bg_data((await cli.get(self.url)).raise_for_status())
                await self.queue.put(x)

    @override
    async def run_tasks(self):
        async with make_http_client() as cli:
            await aio.gather(*(self.task_piece(cli) for _ in range(self.num)))


@bg_provider("loli")
class LoliBGProvider(BaseUrlBGProvider):
    def __init__(self, num: int):
        super().__init__(num, "https://www.loliapi.com/acg/pe/")


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

    async def do_fetch_urls_piece(self, num: int, cli: "AsyncClient"):
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
        async with make_http_client() as cli:
            for x in iter_batch_sizes(self.num, 20):
                await self.do_fetch_urls_piece(x, cli)
        await self.url_queue.put(None)

    async def fetch_image(self, url: str, cli: "AsyncClient"):
        async with self.sem:
            with warning_suppress("Failed to fetch image"):
                bg = resp_to_bg_data((await cli.get(url)).raise_for_status())
                await self.queue.put(bg)

    @override
    async def run_tasks(self):
        pixiv_client = make_http_client(
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


@bg_provider(no_preload=True)
async def local(num: int):
    # we allow providers to return less image than we require
    files = random.sample(BG_FILES, min(num, len(BG_FILES)))
    # logger.debug(f"Chosen background `{files}`")
    for x in files:
        yield BgFileData(
            x,
            mimetypes.guess_type(x)[0] or DEFAULT_MIME,
        )


@bg_provider(no_preload=True)
async def none(num: int):
    for _ in range(num):
        yield create_none_bg()


@bg_provider("url")
class UrlBGProvider(BaseUrlBGProvider):
    def __init__(self, num: int):
        if not config.ps_bg_url:
            raise ValueError("PS_BG_URL is not set")
        super().__init__(num, config.ps_bg_url)


def create_none_bg():
    return BgBytesData(None, DEFAULT_MIME)


async def fetch_bg(
    num: int,
    *,
    fallback_on_error: bool = True,
) -> AsyncIterable[BgData]:
    provider_name = config.ps_bg_provider
    provider = registered_bg_providers.get(provider_name)
    if provider is None:
        logger.error(
            f"Unknown background provider `{config.ps_bg_provider}`, fallback to local",
        )
        async for x in local(num):
            yield x
        return

    try:
        async for x in provider.factory(num):
            yield x
    except Exception as e:
        if not fallback_on_error:
            raise
        log_exception_warning(
            e,
            "Error when getting background, fallback to get one local bg",
        )
        async for x in local(1):
            yield x


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
        if preload_count < 0:
            raise ValueError("preload_count must be non-negative")
        self.preload_count = preload_count
        self.background_queue = aio.Queue[BgData]()
        self.current_load_task_main: aio.Task | None = None
        self.consumed_in_loading: bool = False
        self.fire_tasks: set[aio.Task] = set()
        self.preload_retry_limit = config.ps_bg_preload_retry_limit
        self.fire_return_timeout = config.ps_bg_fire_return_timeout
        self.fire_task_timeout = config.ps_bg_fire_task_timeout
        self.preload_failures = 0
        self.preload_suspended = False
        self.closed = False

    def routine_preload_allowed(self) -> bool:
        provider = registered_bg_providers.get(config.ps_bg_provider)
        return provider is None or not provider.no_preload

    def resume_deferred_preload(self) -> None:
        if self.preload_suspended:
            logger.debug("Resume routine background preload after deferred recovery")
            self.preload_failures = 0
            self.preload_suspended = False

    def record_routine_preload_result(
        self,
        got_candidate: bool,
        exception: Exception | None,
    ) -> None:
        if got_candidate:
            self.preload_failures = 0
            return

        if exception is not None:
            log_exception_warning(exception, "Routine background preload failed")
        else:
            logger.warning("Routine background preload returned no candidates")
        self.preload_failures += 1
        if self.preload_failures >= self.preload_retry_limit:
            self.preload_suspended = True
            logger.debug("Routine background preload retry budget exhausted")

    # we allow fetch_bg return less image than we require
    async def preload_task(
        self,
        count: int,
        fire: bool = False,
        fire_result: aio.Future[BgData | None] | None = None,
    ):
        logger.debug(f"Preload task started, will preload {count} images, {fire=}")
        got_candidate = False
        exception: Exception | None = None
        try:
            async for x in fetch_bg(count, fallback_on_error=fire):
                logger.debug("Got one image")
                got_candidate = True
                if fire and fire_result is not None and not fire_result.done():
                    fire_result.set_result(x)
                    return
                if self.preload_count > 0 or (fire and fire_result is not None):
                    x = cache_bg(x) if isinstance(x, BgBytesData) else x
                await self.background_queue.put(x)
                if fire:
                    return
        except Exception as e:
            exception = e
        else:
            logger.debug("Preload task finished")

        if fire:
            if exception is not None:
                log_exception_warning(exception, "Fire background retrieval failed")
            elif not got_candidate:
                logger.warning("Fire background retrieval returned no candidates")
            if fire_result is not None and not fire_result.done():
                fire_result.set_result(None)
            return

        self.record_routine_preload_result(got_candidate, exception)
        if self.preload_suspended:
            self.current_load_task_main = None
        elif (
            self.consumed_in_loading
            or self.background_queue.qsize() < self.preload_count
        ):
            self.consumed_in_loading = False
            self.current_load_task_main = None
            self.start_preload()
        else:
            self.current_load_task_main = None

    def start_preload(self, force: bool = False):
        if self.closed:
            logger.debug("Background preloader is closed, skip routine preload")
            return
        if self.preload_count == 0:
            logger.debug("Routine background preload disabled by a zero preload target")
            return
        if self.preload_suspended:
            logger.debug("Routine background preload suspended after retry exhaustion")
            return
        if not self.routine_preload_allowed():
            logger.debug("Routine background preload disabled by provider metadata")
            return
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
        loop = aio.get_running_loop()
        result: aio.Future[BgData | None] = loop.create_future()
        timeout_expired = False

        def expire_return_gate() -> None:
            nonlocal timeout_expired
            if not result.done():
                timeout_expired = True
                result.set_result(None)

        async def run_fire_task() -> None:
            try:
                await aio.wait_for(
                    self.preload_task(1, fire=True, fire_result=result),
                    timeout=self.fire_task_timeout,
                )
            except TimeoutError:
                logger.warning("Fire background retrieval exceeded its task deadline")

        fire_task = aio.create_task(run_fire_task())

        def finish_fire_task(task: aio.Task) -> None:
            self.fire_tasks.discard(task)
            if not result.done():
                result.set_result(None)

        fire_task.add_done_callback(finish_fire_task)
        self.fire_tasks.add(fire_task)
        return_gate = loop.call_later(self.fire_return_timeout, expire_return_gate)
        try:
            bg = await result
        finally:
            return_gate.cancel()

        if bg is not None and (
            (not isinstance(bg, BgFileData)) or (bg := read_cached_bg_file(bg))
        ):
            return bg

        if timeout_expired:
            logger.warning("Fire background retrieval timed out, falling back to local")
        elif bg is not None:
            logger.warning("Fire background retrieval returned an unreadable image")
        return await get_one_fallback()

    async def get(self) -> BgBytesData:
        if self.closed:
            return await get_one_fallback()
        self.resume_deferred_preload()
        self.set_defer_preload()

        while not self.background_queue.empty():
            bg = await self.background_queue.get()
            self.set_defer_preload()
            if (not isinstance(bg, BgFileData)) or (bg := read_cached_bg_file(bg)):
                return bg

        # normally all items in queue should be valid
        # if they not, we should fetch
        return await self._get_on_fire()

    async def close(self) -> None:
        if self.closed:
            return
        self.closed = True
        tasks = set(self.fire_tasks)
        if self.current_load_task_main is not None:
            tasks.add(self.current_load_task_main)
        for task in tasks:
            task.cancel()
        if tasks:
            await aio.gather(*tasks, return_exceptions=True)
        self.fire_tasks.difference_update(tasks)
        self.current_load_task_main = None


bg_preloader = BgPreloader(config.ps_bg_preload_count)

driver = get_driver()


@driver.on_shutdown
async def _():
    await bg_preloader.close()
