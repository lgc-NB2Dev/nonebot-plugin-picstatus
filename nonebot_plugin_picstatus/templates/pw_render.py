import mimetypes
import re
from contextlib import asynccontextmanager
from dataclasses import dataclass
from functools import wraps
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, TypeVar, Union
from urllib.parse import urlencode

import anyio
import jinja2
from cookit import auto_convert_byte
from nonebot import logger
from nonebot_plugin_htmlrender import get_new_page
from playwright.async_api import Page, Request, Route
from yarl import URL

from ..bg_provider import get_bg
from ..config import DEFAULT_AVATAR_PATH, config
from ..statistics import bot_avatar_cache, bot_info_cache
from ..util import format_cpu_freq

PatternType = Union[re.Pattern, str]
RouterType = Callable[[Route, Request], Any]
TR = TypeVar("TR", bound=RouterType)
TC = TypeVar("TC", bound=Callable[..., Any])

ROOT_PATH = Path(__file__).parent.parent
RES_PATH = ROOT_PATH / "res"
TEMPLATES_PATH = ROOT_PATH / "templates"
ROUTE_URL = "http://picstatus.nonebot"
RES_LOCATION_MAP = {
    "": RES_PATH,
}


@dataclass
class RouterData:
    pattern: PatternType
    func: RouterType
    priority: int


registered_routers: List[RouterData] = []
global_jinja_filters: Dict[str, Callable] = {}


def resolve_file_url(
    path: str,
    additional_locations: Optional[Dict[str, Path]] = None,
) -> str:
    if path.startswith("res:"):
        path = path[4:].lstrip("/")
        locations = {**RES_LOCATION_MAP, **(additional_locations or {})}
        for pfx, loc in locations.items():
            if (loc / path).exists():
                return f"/{pfx}/{path}"
        raise ValueError(f"Cannot resolve builtin resource `{path}`")
    params = urlencode({"path": path})
    return f"/api/local_file?{params}"


def jinja_filter(func: TC, name: str = "") -> TC:
    name = name or func.__name__
    if name in global_jinja_filters:
        raise ValueError(f"Duplicate filter name `{name}`")
    global_jinja_filters[name] = func
    logger.debug(f"Registered global jinja filter `{name}`")
    return func


def register_global_filter_to(env: jinja2.Environment):
    for name, func in global_jinja_filters.items():
        env.filters[name] = func


def router(pattern: PatternType, priority: int = 0):
    def wrapper(func: TR) -> TR:
        @wraps(func)
        async def wrapped_func(route: Route, request: Request):
            logger.debug(
                f"Requested routed URL `{request.url}`, Handling route `{pattern}`",
            )
            try:
                return await func(route, request)
            except Exception:
                logger.exception(f"Error occurred when handling route `{pattern}`")
                await route.abort()

        registered_routers.append(RouterData(pattern, wrapped_func, priority))
        return func

    return wrapper


@asynccontextmanager
async def get_routed_page(**kwargs) -> AsyncIterator[Page]:
    async with get_new_page(**kwargs) as page:
        # 低 priority 的 router 应最先运行。因为 playwright 后 route 的先运行，所以要反过来排序
        for x in sorted(registered_routers, key=lambda x: x.priority, reverse=True):
            await page.route(x.pattern, x.func)
        await page.goto(ROUTE_URL)
        yield page


def file_router(
    query_name: Optional[str] = None,
    base_path: Optional[Path] = None,
    prefix_omit: str = "",
) -> RouterType:
    async def router(route: Route, request: Request):
        url = URL(request.url)
        query_path = url.query.get(query_name, "") if query_name else url.path[1:]
        if prefix_omit and query_path.startswith(prefix_omit):
            query_path = query_path[len(prefix_omit) :]
        path = anyio.Path((base_path / query_path) if base_path else query_path)
        logger.debug(f"Associated file `{path}`")
        if not await path.exists():
            await route.abort()
            return
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        await route.fulfill(content_type=content_type, body=await path.read_bytes())

    return router


jinja_filter(format_cpu_freq)


@jinja_filter
def percent_to_color(percent: float) -> str:
    if percent < 70:
        return "prog-low"
    if percent < 90:
        return "prog-medium"
    return "prog-high"


@jinja_filter
def auto_convert_unit(value: float, **kw) -> str:
    return auto_convert_byte(value=value, with_space=False, **kw)


@jinja_filter
def br(text: str) -> str:
    return text.replace("\n", "<br>")


@router(f"{ROUTE_URL}/")
async def _(route: Route, _: Request):
    await route.fulfill(content_type="text/html", body="<html></html>")


@router(f"{ROUTE_URL}/api/background")
async def _(route: Route, _: Request):
    data = await get_bg()
    await route.fulfill(body=data)


@router(f"{ROUTE_URL}/api/bot_avatar/*")
async def _(route: Route, request: Request):
    url = URL(request.url)
    self_id = url.parts[-1]

    if self_id in bot_avatar_cache:
        await route.fulfill(body=bot_avatar_cache[self_id])
        return

    if (self_id in bot_info_cache) and (avatar := bot_info_cache[self_id].user_avatar):
        try:
            img = await avatar.get_image()
        except Exception as e:
            logger.warning(
                f"Error when getting bot avatar, fallback to default: "
                f"{e.__class__.__name__}: {e}",
            )
        else:
            bot_avatar_cache[self_id] = img
            await route.fulfill(body=img)
            return

    data = (
        config.ps_default_avatar
        if config.ps_default_avatar.is_file()
        else DEFAULT_AVATAR_PATH
    ).read_bytes()
    await route.fulfill(body=data)


router(f"{ROUTE_URL}/api/local_file*")(
    file_router(query_name="path", base_path=None),
)

for p in TEMPLATES_PATH.iterdir():
    if not p.is_dir():
        continue
    router(f"{ROUTE_URL}/{p.name}/res/**/*", priority=99)(
        file_router(query_name=None, base_path=p / "res", prefix_omit=f"{p.name}/res/"),
    )

router(f"{ROUTE_URL}/**/*", priority=100)(
    file_router(query_name=None, base_path=RES_PATH),
)
