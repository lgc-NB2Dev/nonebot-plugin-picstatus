# ruff: noqa: E402

import json
from collections import deque
from pathlib import Path
from typing import TYPE_CHECKING, Any

import jinja2 as jj
from cookit.jinja import make_register_jinja_filter_deco
from nonebot import get_plugin_config, require
from nonebot_plugin_picstatus.templates import pic_template
from nonebot_plugin_picstatus.templates.pw_render import (
    ROUTE_URL,
    add_background_router,
    add_root_router,
    base_router_group,
    register_global_filter_to,
)
from pydantic import BaseModel

# 添加自定义图片模板示例
# 示例应用例请见 https://github.com/lgc-NB2Dev/nonebot-plugin-picstatus/blob/master/nonebot_plugin_picstatus/templates/default/__init__.py

# 可以使用你喜欢的任意库来绘图
# 示例使用 playwright，你也可以使用 Pillow 等
# 本插件中自带一些使用 playwright 时绘图有帮助的工具函数
# 详见 https://github.com/lgc-NB2Dev/nonebot-plugin-picstatus/blob/master/nonebot_plugin_picstatus/templates/pw_render.py

require("nonebot_plugin_htmlrender")

from nonebot_plugin_htmlrender import get_new_page

if TYPE_CHECKING:
    from nonebot_plugin_picstatus.bg_provider import BgBytesData

RES_DIR = Path(__file__).parent / "res"

template_env = jj.Environment(
    loader=jj.FileSystemLoader(RES_DIR),
    autoescape=True,
    enable_async=True,
)
# 将插件提供的实用模板 filter 注册到模板环境中
register_global_filter_to(template_env)


jinja_filter = make_register_jinja_filter_deco(template_env)


@jinja_filter
def json_dumps(obj: Any, **kwargs) -> str:
    if isinstance(obj, dict):
        obj = {k: list(v) if isinstance(v, deque) else v for k, v in obj.items()}
    return json.dumps(obj, **kwargs)


# 复制一份插件自带的路由组以便在该份代码范围中增删
template_router_group = base_router_group.copy()


# 可以把模板特定配置项声明在这里
# 你也可以不在这里写，换成写到插件的 config.py 文件中，看个人喜好了
class TemplateConfig(BaseModel):
    ps_example_template_example_config: str | None = "example"


template_config = get_plugin_config(TemplateConfig)


# 注册模板渲染函数
# name 参数为模板名称，不提供时使用函数名
# collecting 传入需要启用的 collector 名称集合，如不提供则启用所有 collector
@pic_template(
    collecting={
        "counter",
        "first_time_counter",
        "periodic_counter",
        "time_counter",
    },
)
async def example_template(collected: dict[str, Any], bg: "BgBytesData", **_):
    template = template_env.get_template("index.html.jinja")
    html = await template.render_async(d=collected, config=template_config)

    # copy 一份以添加这次图片渲染中特定的 router
    router_group = template_router_group.copy()
    add_root_router(router_group, html)  # 注册根路由，访问返回渲好的 html
    add_background_router(router_group, bg)  # 注册背景图片路由

    async with get_new_page() as page:
        await router_group.apply(page)
        await page.goto(f"{ROUTE_URL}/", wait_until="load")
        elem = await page.wait_for_selector("main")
        assert elem
        return await elem.screenshot(type="jpeg")
