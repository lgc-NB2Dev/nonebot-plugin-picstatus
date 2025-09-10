# ruff: noqa: E402

from nonebot import get_driver, require
from nonebot.plugin import PluginMetadata, inherit_supported_adapters

require("nonebot_plugin_apscheduler")
require("nonebot_plugin_alconna")
require("nonebot_plugin_uninfo")
require("nonebot_plugin_localstore")

from . import __main__ as __main__, misc_statistics as misc_statistics
from .bg_provider import bg_preloader
from .collectors import (
    enable_collectors,
    load_builtin_collectors,
    registered_collectors,
)
from .config import ConfigModel, config
from .templates import load_builtin_templates, loaded_templates

driver = get_driver()


# lazy load builtin templates and collectors
@driver.on_startup
async def _():
    if config.ps_template not in loaded_templates:
        load_builtin_templates()
    current_template = loaded_templates.get(config.ps_template)
    if current_template is None:
        raise ValueError(f"Template {config.ps_template} not found")

    if (current_template.collectors is None) or any(
        (x not in registered_collectors) for x in current_template.collectors
    ):
        load_builtin_collectors()

    collectors = (
        set(registered_collectors)
        if current_template.collectors is None
        else current_template.collectors
    )
    await enable_collectors(*collectors)

    bg_preloader.start_preload()


usage = f"指令：{' / '.join(config.ps_command)}"
if config.ps_need_at:
    usage += "\n注意：使用指令时需要@机器人"
if config.ps_only_su:
    usage += "\n注意：仅SuperUser可以使用此指令"

__version__ = "2.2.1"
__plugin_meta__ = PluginMetadata(
    name="PicStatus",
    description="以图片形式显示当前设备的运行状态",
    usage=usage,
    type="application",
    homepage="https://github.com/lgc-NB2Dev/nonebot-plugin-picstatus",
    config=ConfigModel,
    supported_adapters=inherit_supported_adapters(
        "nonebot_plugin_alconna",
        "nonebot_plugin_uninfo",
    ),
    extra={"License": "MIT", "Author": "LgCookie"},
)
