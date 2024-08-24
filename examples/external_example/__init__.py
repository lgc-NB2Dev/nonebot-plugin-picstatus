# ruff: noqa: E402

from nonebot import require

require("nonebot_plugin_picstatus")  # 别忘 require

from . import (
    bg_provider as bg_provider,
    collectors as collectors,
    templates as templates,
)
