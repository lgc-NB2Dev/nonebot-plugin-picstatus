# ruff: noqa: E402

from nonebot import require
from nonebot.plugin import PluginMetadata, inherit_supported_adapters

require("nonebot_plugin_apscheduler")
require("nonebot_plugin_alconna")
require("nonebot_plugin_userinfo")
require("nonebot_plugin_htmlrender")

from . import __main__ as __main__, statistics as statistics
from .collectors import enable_collectors, load_collectors
from .config import ConfigModel, config
from .templates import load_template

load_collectors()
try:
    _template = load_template(config.ps_template)
except ImportError as e:
    raise ImportError(f"Cannot found template `{config.ps_template}`") from e
enable_collectors(*_template.collectors)


usage = f"指令：{' / '.join(config.ps_command)}"
if config.ps_need_at:
    usage += "\n注意：使用指令时需要@机器人"
if config.ps_only_su:
    usage += "\n注意：仅SuperUser可以使用此指令"

__version__ = "2.0.0.post2"
__plugin_meta__ = PluginMetadata(
    name="PicStatus",
    description="以图片形式显示当前设备的运行状态",
    usage=usage,
    type="application",
    homepage="https://github.com/lgc-NB2Dev/nonebot-plugin-picstatus",
    config=ConfigModel,
    supported_adapters=inherit_supported_adapters("nonebot_plugin_alconna"),
    extra={"License": "MIT", "Author": "student_2333"},
)
