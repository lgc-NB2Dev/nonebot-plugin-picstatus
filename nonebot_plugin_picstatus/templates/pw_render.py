from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeVar
from urllib.parse import urlencode

from cookit import auto_convert_byte
from cookit.jinja import all_filters
from cookit.jinja.filters import cookit_global_filter
from cookit.pw import CKRouterFunc, RouterGroup, make_real_path_router
from cookit.pw.loguru import log_router_err
from nonebot import logger
from yarl import URL

from ..config import DEFAULT_AVATAR_PATH, config
from ..misc_statistics import bot_avatar_cache
from ..util import format_cpu_freq

if TYPE_CHECKING:
    import jinja2
    from playwright.async_api import Request, Route

    from ..bg_provider import BgBytesData

TC = TypeVar("TC", bound=Callable[..., Any])

ROOT_PATH = Path(__file__).parent.parent
RES_PATH = ROOT_PATH / "res"
ROUTE_URL = "http://picstatus.nonebot"
RES_LOCATION_MAP = {
    "": RES_PATH,
}

# region pw

base_router_group = RouterGroup()


def resolve_file_url(
    path: str,
    additional_locations: dict[str, Path] | None = None,
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


def make_file_router(
    query_name: str | None = None,
    base_path: Path | None = None,
    prefix_omit: str = "",
) -> CKRouterFunc:
    @log_router_err()
    @make_real_path_router
    async def router(request: "Request", **_):
        url = URL(request.url)
        query_path = url.query.get(query_name, "") if query_name else url.path[1:]
        if prefix_omit and query_path.startswith(prefix_omit):
            query_path = query_path[len(prefix_omit) :]
        path = Path((base_path / query_path) if base_path else query_path)
        logger.debug(f"Associated file `{path}`")
        return path

    return router


@base_router_group.router(f"{ROUTE_URL}/api/bot_avatar/*")
@log_router_err()
async def _(route: "Route", request: "Request", **_):
    url = URL(request.url)
    self_id = url.parts[-1]

    if self_id in bot_avatar_cache:
        await route.fulfill(body=bot_avatar_cache[self_id])
        return

    data = (
        config.ps_default_avatar
        if config.ps_default_avatar.is_file()
        else DEFAULT_AVATAR_PATH
    ).read_bytes()
    await route.fulfill(body=data)


base_router_group.router(f"{ROUTE_URL}/api/local_file*")(
    make_file_router(query_name="path", base_path=None),
)

base_router_group.router(f"{ROUTE_URL}/**/*", priority=100)(
    make_file_router(query_name=None, base_path=RES_PATH),
)


def add_root_router(router_group: RouterGroup, html: str):
    @router_group.router(f"{ROUTE_URL}/")
    @log_router_err()
    async def _(route: "Route", **_):
        await route.fulfill(content_type="text/html", body=html)


def add_background_router(router_group: RouterGroup, bg: "BgBytesData"):
    @router_group.router(f"{ROUTE_URL}/api/background")
    @log_router_err()
    async def _(route: "Route", **_):
        await route.fulfill(content_type=bg.mime, body=bg.data)


# endregion

# region jinja


jinja_filter = type(cookit_global_filter)(all_filters.copy())


def register_global_filter_to(env: "jinja2.Environment"):
    env.filters.update(jinja_filter.data)


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


# endregion
