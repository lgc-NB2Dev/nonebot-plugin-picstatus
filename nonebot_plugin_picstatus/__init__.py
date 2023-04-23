from nonebot.plugin import PluginMetadata

from . import __main__ as __main__
from . import statistics as statistics
from .config import Cfg, config
from .version import __version__ as __version__

usage = "指令：运行状态 | 状态"
if config.ps_need_at:
    usage += "\n注意：使用指令时需要@机器人"
if config.ps_only_su:
    usage += "\n注意：仅SuperUser可以使用此指令"

__plugin_meta__ = PluginMetadata(
    name="PicStatus",
    description="以图片形式显示当前设备的运行状态",
    usage=usage,
    config=Cfg,
)
