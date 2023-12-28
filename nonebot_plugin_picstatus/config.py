from pathlib import Path
from typing import List, Literal, Optional, Set

from nonebot import get_driver
from pydantic import AnyHttpUrl, BaseModel, Field

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


DEFAULT_COMPONENTS = ["header", "cpu_mem", "disk", "network", "process", "footer"]
DEFAULT_COMMANDS = ["运行状态", "状态", "zt", "yxzt", "status"]
DEFAULT_IGNORE_NETS = [r"^lo(op)?\d*$", "^Loopback"]
DEFAULT_TEST_SITES = [
    TestSiteCfg.parse_obj({"name": "百度", "url": "https://www.baidu.com/"}),
    TestSiteCfg.parse_obj(
        {"name": "Google", "url": "https://www.google.com/", "use_proxy": True},
    ),
]
DEFAULT_IGNORE_PROCS = ["^System Idle Process$"]


class Cfg(BaseModel):
    # region builtin
    superusers: Set[str]
    nickname: Set[str]
    # endregion

    # region global
    proxy: Optional[str] = None
    # endregion

    # region behavior
    ps_command: List[str] = Field(default_factory=lambda: DEFAULT_COMMANDS)
    ps_only_su: bool = False
    ps_need_at: bool = False
    ps_reply_target: bool = True
    ps_req_timeout: Optional[int] = 10
    # endregion

    # region style
    ps_components: List[str] = Field(default_factory=lambda: DEFAULT_COMPONENTS)
    ps_additional_css: List[str] = Field(default_factory=list)
    ps_additional_script: List[str] = Field(default_factory=list)
    ps_bg_provider: str = "gm"
    ps_default_avatar: Path = DEFAULT_AVATAR_PATH
    ps_bg_path: Path = DEFAULT_BG_PATH
    # endregion

    # region components
    # region header
    ps_use_env_nick: bool = False
    ps_show_current_bot_only: bool = False
    # endregion

    # region disk
    # usage
    ps_ignore_parts: List[str] = Field(default_factory=list)
    ps_ignore_bad_parts: bool = False
    ps_sort_parts: bool = True
    ps_sort_parts_reverse: bool = False
    # io
    ps_ignore_disk_ios: List[str] = Field(default_factory=list)
    ps_ignore_no_io_disk: bool = False
    ps_sort_disk_ios: bool = True
    # endregion

    # region net
    # io
    ps_ignore_nets: List[str] = Field(default_factory=lambda: DEFAULT_IGNORE_NETS)
    ps_ignore_0b_net: bool = False
    ps_sort_nets: bool = True
    # connection_test
    ps_test_sites: List[TestSiteCfg] = Field(default_factory=lambda: DEFAULT_TEST_SITES)
    ps_sort_sites: bool = True
    ps_test_timeout: int = 5
    # endregion

    # region process
    ps_proc_len: int = 5
    ps_ignore_procs: List[str] = Field(default_factory=lambda: DEFAULT_IGNORE_PROCS)
    ps_proc_sort_by: ProcSortByType = "cpu"
    ps_proc_cpu_max_100p: bool = False
    # endregion
    # endregion components


config: Cfg = Cfg.parse_obj(get_driver().config.dict())
