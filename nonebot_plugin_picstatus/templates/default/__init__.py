from pathlib import Path
from typing import Any, Dict, List

import jinja2
from cookit import SizedList
from cookit.pyd import field_validator
from pydantic import BaseModel

from ..pw_render import get_routed_page, register_global_filter_to, resolve_file_url

collecting = "all"

RES_PATH = Path(__file__).parent / "res"
TEMPLATE_PATH = RES_PATH / "templates"
CSS_PATH = RES_PATH / "css"
ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(TEMPLATE_PATH)),
    autoescape=jinja2.select_autoescape(["html", "xml"]),
    enable_async=True,
)
register_global_filter_to(ENVIRONMENT)


class TemplateConfig(BaseModel):
    ps_default_components: List[str] = [
        "header",
        "cpu_mem",
        "disk",
        "network",
        "process",
        "footer",
    ]
    ps_default_additional_css: List[str] = []
    ps_default_additional_script: List[str] = []

    @field_validator("ps_default_additional_css")
    def resolve_css_url(cls, v: List[str]):  # noqa: N805
        return [resolve_file_url(x, {"default/res/css": CSS_PATH}) for x in v]

    @field_validator("ps_default_additional_script")
    def resolve_script_url(cls, v: List[str]):  # noqa: N805
        return [resolve_file_url(x) for x in v]


async def render(collected: Dict[str, Any], config: TemplateConfig) -> bytes:
    collected = {
        k: v[0] if isinstance(v, SizedList) else v for k, v in collected.items()
    }
    template = ENVIRONMENT.get_template("index.html.jinja")
    html = await template.render_async(d=collected, config=config)
    if (p := Path.cwd() / "picstatus-debug.html").exists():
        p.write_text(html, "u8")
    async with get_routed_page() as page:
        await page.set_content(html)
        await page.wait_for_selector("body.done")
        elem = await page.query_selector(".main-background")
        assert elem
        return await elem.screenshot(type="jpeg")
