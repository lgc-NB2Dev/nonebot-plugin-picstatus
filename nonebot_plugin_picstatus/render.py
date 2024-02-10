import asyncio
import mimetypes
import re
from contextlib import asynccontextmanager
from dataclasses import dataclass
from functools import wraps
from pathlib import Path
from typing import Any, AsyncIterator, Callable, List, Optional, TypeVar, Union
from urllib.parse import urlencode

import anyio
import jinja2
from nonebot import logger
from nonebot_plugin_htmlrender import get_new_page
from playwright.async_api import Page, Request, Route
from yarl import URL

from .bg_provider import get_bg
from .components import ComponentType, components
from .config import TEMPLATE_PATH, config
from .util import auto_convert_unit, percent_to_color

PatternType = Union[re.Pattern, str]
RouterType = Callable[[Route, Request], Any]
TR = TypeVar("TR", bound=RouterType)
TC = TypeVar("TC", bound=Callable[..., Any])

RES_PATH = Path(__file__).parent / "res"
ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(TEMPLATE_PATH)),
    autoescape=jinja2.select_autoescape(["html", "xml"]),
    enable_async=True,
)
ROUTE_URL = "http://picstatus.nonebot"


@dataclass
class RouterData:
    pattern: PatternType
    func: RouterType
    priority: int


registered_routers: List[RouterData] = []


def resolve_file_url(path: str, prefix: str = "") -> str:
    if not prefix.startswith("/"):
        prefix = f"/{prefix}"
    if prefix.endswith("/"):
        prefix = prefix[:-1]

    if path.startswith("res:"):
        return f"{prefix}/{path[4:]}"
    params = urlencode({"path": f"{prefix}/{path}"})
    return f"/api/local_file?{params}"


def jinja_filter(func: TC) -> TC:
    name = func.__name__
    if name in ENVIRONMENT.filters:
        raise ValueError(f"Duplicate filter name `{name}`")
    ENVIRONMENT.filters[name] = func
    return func


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


async def render_image(main_content: str) -> bytes:
    html = await ENVIRONMENT.get_template("index.html.jinja").render_async(
        main=main_content,
        additional_css=[resolve_file_url(x, "css") for x in config.ps_additional_css],
        additional_script=[
            resolve_file_url(x, "js") for x in config.ps_additional_script
        ],
    )
    if (p := (Path.cwd() / "picstatus-debug.html")).exists():
        p.write_text(html, encoding="u8")
    async with get_routed_page() as page:
        await page.set_content(html)
        await page.wait_for_selector("body.done")
        elem = await page.query_selector(".main-background")
        assert elem
        return await elem.screenshot(type="jpeg")


async def collect_and_render() -> bytes:
    selected: List[ComponentType] = []
    for name in config.ps_components:
        if name not in components:
            logger.warning(f"Component `{name}` not found")
            continue
        selected.append(components[name])

    contents = await asyncio.gather(*(x() for x in selected))
    main_html = "\n".join(contents)
    return await render_image(main_html)


def file_router(
    query_name: Optional[str] = None,
    base_path: Optional[Path] = None,
) -> RouterType:
    async def router(route: Route, request: Request):
        url = URL(request.url)
        query_path = url.query.get(query_name, "") if query_name else url.path[1:]
        path = anyio.Path((base_path / query_path) if base_path else query_path)
        logger.debug(f"Associated file `{path}`")
        if not await path.exists():
            await route.abort()
            return
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        await route.fulfill(content_type=content_type, body=await path.read_bytes())

    return router


jinja_filter(auto_convert_unit)
jinja_filter(percent_to_color)


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


router(f"{ROUTE_URL}/api/local_file*")(
    file_router(query_name="path", base_path=None),
)

router(f"{ROUTE_URL}/**/*", priority=99)(
    file_router(query_name=None, base_path=RES_PATH),
)
