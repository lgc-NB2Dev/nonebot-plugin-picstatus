from collections import deque
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

import jinja2
from cookit import flatten
from cookit.pyd import field_validator
from nonebot import get_plugin_config, require
from pydantic import BaseModel

from ...util import debug
from .. import pic_template
from ..pw_render import (
    ROUTE_URL,
    add_background_router,
    add_root_router,
    base_router_group,
    make_file_router,
    register_global_filter_to,
    resolve_file_url,
)

require("nonebot_plugin_htmlrender")

from nonebot_plugin_htmlrender import get_new_page  # noqa: E402

if TYPE_CHECKING:
    from ...bg_provider import BgData

RES_PATH = Path(__file__).parent / "res"
TEMPLATE_PATH = RES_PATH / "templates"
CSS_PATH = RES_PATH / "css"
ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(TEMPLATE_PATH)),
    autoescape=jinja2.select_autoescape(["html", "xml"]),
    enable_async=True,
)
register_global_filter_to(ENVIRONMENT)

template_router_group = base_router_group.copy()
template_router_group.router(f"{ROUTE_URL}/default/res/**/*", priority=99)(
    make_file_router(query_name=None, base_path=RES_PATH, prefix_omit="default/res/"),
)

COMPONENT_COLLECTORS = {
    "header": {"bots", "nonebot_run_time", "system_run_time"},
    "cpu_mem": {
        "cpu_percent",
        "cpu_count",
        "cpu_count_logical",
        "cpu_freq",
        "cpu_brand",
        "memory_stat",
        "swap_stat",
    },
    "disk": {"disk_usage", "disk_io"},
    "network": {"network_io", "network_connection"},
    "process": {"process_status"},
    "footer": {
        "nonebot_version",
        "ps_version",
        "time",
        "python_version",
        "system_name",
    },
}


class TemplateConfig(BaseModel):
    ps_default_components: list[str] = [
        "header",
        "cpu_mem",
        "disk",
        "network",
        "process",
        "footer",
    ]
    ps_default_additional_css: list[str] = []
    ps_default_additional_script: list[str] = []
    ps_default_pic_format: Literal["jpeg", "png"] = "jpeg"

    @field_validator("ps_default_additional_css")
    def resolve_css_url(cls, v: list[str]):  # noqa: N805
        return [resolve_file_url(x, {"default/res/css": CSS_PATH}) for x in v]

    @field_validator("ps_default_additional_script")
    def resolve_script_url(cls, v: list[str]):  # noqa: N805
        return [resolve_file_url(x) for x in v]


template_config = get_plugin_config(TemplateConfig)
collecting = set(
    flatten(COMPONENT_COLLECTORS[k] for k in template_config.ps_default_components),
)


@pic_template(collecting=collecting)
async def default(collected: dict[str, Any], bg: "BgData", **_) -> bytes:
    collected = {k: v[0] if isinstance(v, deque) else v for k, v in collected.items()}
    template = ENVIRONMENT.get_template("index.html.jinja")
    html = await template.render_async(d=collected, config=template_config)

    if debug.enabled:
        debug.write(html, "default_{time}.html")

    router_group = template_router_group.copy()
    add_root_router(router_group, html)
    add_background_router(router_group, bg)

    async with get_new_page() as page:
        await router_group.apply(page)
        await page.goto(f"{ROUTE_URL}/")
        await page.wait_for_selector("body.done")
        elem = await page.query_selector(".main-background")
        assert elem
        return await elem.screenshot(type="jpeg")
