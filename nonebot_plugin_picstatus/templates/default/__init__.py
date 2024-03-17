from pathlib import Path
from typing import Any, Dict, List

import jinja2
from cookit import SizedList
from pydantic import BaseModel

from ..pw_render import get_routed_page, register_filter_to

collecting = "all"

TEMPLATE_PATH = Path(__file__).parent / "res" / "templates"
ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(TEMPLATE_PATH)),
    autoescape=jinja2.select_autoescape(["html", "xml"]),
    enable_async=True,
)


class TemplateConfig(BaseModel):
    ps_components: List[str] = [
        "header",
        "cpu_mem",
        "disk",
        "network",
        "process",
        "footer",
    ]
    ps_additional_css: List[str] = []
    ps_additional_script: List[str] = []


async def render(collected: Dict[str, Any], config: TemplateConfig) -> bytes:
    collected = {
        k: v[0] if isinstance(v, SizedList) else v for k, v in collected.items()
    }
    template = ENVIRONMENT.get_template("index.html.jinja")
    html = await template.render_async(d=collected, config=config)
    async with get_routed_page() as page:
        await page.set_content(html)
        await page.wait_for_selector("body.done")
        elem = await page.query_selector(".main-background")
        assert elem
        return await elem.screenshot(type="jpeg")


register_filter_to(ENVIRONMENT)
