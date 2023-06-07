from nonebot import require
from nonebot.plugin import PluginMetadata

require("nonebot_plugin_saa")

from . import __main__ as __main__  # noqa: E402
from . import statistics as statistics  # noqa: E402
from .config import Cfg, config  # noqa: E402
from .version import __version__ as __version__  # noqa: E402

usage = "指令：运行状态 / 状态 / yxzt / zt / status"
if config.ps_need_at:
    usage += "\n注意：使用指令时需要@机器人"
if config.ps_only_su:
    usage += "\n注意：仅SuperUser可以使用此指令"

__plugin_meta__ = PluginMetadata(
    name="PicStatus",
    description="以图片形式显示当前设备的运行状态",
    usage=usage,
    type="application",
    homepage="https://github.com/lgc-NB2Dev/nonebot-plugin-picstatus",
    config=Cfg,
    supported_adapters={
        "~onebot.v11",
        "~onebot.v12",
        "~telegram",
        "~kaiheila",
        "~qqguild",
    },
    extra={"License": "MIT", "Author": "student_2333"},
)
