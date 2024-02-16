from pathlib import Path
from typing import List, Literal, Optional, Set

from nonebot import get_plugin_config
from nonebot.compat import type_validate_python
from pydantic import AnyHttpUrl, BaseModel

RES_PATH = Path(__file__).parent / "res"
ASSETS_PATH = RES_PATH / "assets"
TEMPLATE_PATH = RES_PATH / "templates"
DEFAULT_BG_PATH = ASSETS_PATH / "default_bg.webp"
DEFAULT_AVATAR_PATH = ASSETS_PATH / "default_avatar.webp"

ProcSortByType = Literal["cpu", "mem"]


class TestSiteCfg(BaseModel):
    name: str
    url: AnyHttpUrl
    use_proxy: bool = False


class Cfg(BaseModel):
    # region builtin
    superusers: Set[str]
    nickname: Set[str]
    # endregion

    # region global
    proxy: Optional[str] = None
    # endregion

    # region behavior
    ps_command: List[str] = ["运行状态", "状态", "zt", "yxzt", "status"]
    ps_only_su: bool = False
    ps_need_at: bool = False
    ps_reply_target: bool = True
    ps_req_timeout: Optional[int] = 10
    # endregion

    # region style
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
    ps_bg_provider: str = "gm"
    ps_bg_lolicon_r18_type: Literal[0, 1, 2] = 0
    ps_bg_local_path: Path = DEFAULT_BG_PATH
    ps_default_avatar: Path = DEFAULT_AVATAR_PATH
    # endregion

    # region components
    # region header
    ps_use_env_nick: bool = False
    ps_show_current_bot_only: bool = False
    ps_ob_v11_use_get_status: bool = True
    # endregion

    # region disk
    # usage
    ps_ignore_parts: List[str] = []
    ps_ignore_bad_parts: bool = False
    ps_sort_parts: bool = True
    ps_sort_parts_reverse: bool = False
    # io
    ps_ignore_disk_ios: List[str] = []
    ps_ignore_no_io_disk: bool = False
    ps_sort_disk_ios: bool = True
    # endregion

    # region network
    # io
    ps_ignore_nets: List[str] = [r"^lo(op)?\d*$", "^Loopback"]
    ps_ignore_0b_net: bool = False
    ps_sort_nets: bool = True
    # connection_test
    ps_test_sites: List[TestSiteCfg] = [
        type_validate_python(
            TestSiteCfg,
            {"name": "百度", "url": "https://www.baidu.com/"},
        ),
        type_validate_python(
            TestSiteCfg,
            {"name": "Google", "url": "https://www.google.com/", "use_proxy": True},
        ),
    ]
    ps_sort_sites: bool = True
    ps_test_timeout: int = 5
    # endregion

    # region process
    ps_proc_len: int = 5
    ps_ignore_procs: List[str] = ["^System Idle Process$"]
    ps_proc_sort_by: ProcSortByType = "cpu"
    ps_proc_cpu_max_100p: bool = False
    # endregion
    # endregion components


config: Cfg = get_plugin_config(Cfg)
