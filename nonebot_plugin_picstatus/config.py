import shutil
from pathlib import Path
from typing import Literal

from cookit.nonebot.localstore import ensure_localstore_path_config
from nonebot import get_plugin_config
from nonebot.compat import type_validate_python
from nonebot_plugin_localstore import get_plugin_cache_dir
from pydantic import AnyHttpUrl, BaseModel, Field

ensure_localstore_path_config()

CACHE_DIR = get_plugin_cache_dir()

BG_PRELOAD_CACHE_DIR = CACHE_DIR / "bg_preload"
if BG_PRELOAD_CACHE_DIR.exists():
    shutil.rmtree(BG_PRELOAD_CACHE_DIR)
BG_PRELOAD_CACHE_DIR.mkdir(parents=True, exist_ok=True)

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


class ConfigModel(BaseModel):
    # region builtin
    superusers: set[str]
    nickname: set[str]
    # endregion

    # region global
    proxy: str | None = None
    # endregion

    # region behavior
    ps_template: str = "default"
    ps_command: list[str] = ["运行状态", "状态", "zt", "yxzt", "status"]
    ps_only_su: bool = False
    ps_need_at: bool = False
    ps_reply_target: bool = True
    ps_req_timeout: int | None = 10
    # endregion

    # region style
    ps_bg_provider: str = "loli"
    ps_bg_preload_count: int = 2
    ps_bg_lolicon_r18_type: Literal[0, 1, 2] = 0
    ps_bg_local_path: Path = DEFAULT_BG_PATH
    ps_default_avatar: Path = DEFAULT_AVATAR_PATH
    # endregion

    # region collectors
    # region base
    ps_collect_interval: int = 5
    ps_default_collect_cache_size: int = 1
    ps_collect_cache_size: dict[str, int] = Field(default_factory=dict)
    # endregion

    # region header
    ps_use_env_nick: bool = False
    ps_show_current_bot_only: bool = False
    ps_ob_v11_use_get_status: bool = True
    ps_count_message_sent_event: bool | set[str] = False
    ps_disconnect_reset_counter: bool = True
    # endregion

    # region disk
    # usage
    ps_ignore_parts: list[str] = []
    ps_ignore_bad_parts: bool = False
    ps_sort_parts: bool = True
    ps_sort_parts_reverse: bool = False
    # io
    ps_ignore_disk_ios: list[str] = [r"^(loop|zram)\d*$"]
    ps_ignore_no_io_disk: bool = False
    ps_sort_disk_ios: bool = True
    # endregion

    # region network
    # io
    ps_ignore_nets: list[str] = [r"^lo(op)?\d*$|^(Loopback|本地连接)"]
    ps_ignore_0b_net: bool = False
    ps_sort_nets: bool = True
    # connection_test
    ps_test_sites: list[TestSiteCfg] = [  # v1 compat #59
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
    ps_ignore_procs: list[str] = ["^System Idle Process$"]
    ps_proc_sort_by: ProcSortByType = "cpu"
    ps_proc_cpu_max_100p: bool = False
    # endregion
    # endregion components


config: ConfigModel = get_plugin_config(ConfigModel)
