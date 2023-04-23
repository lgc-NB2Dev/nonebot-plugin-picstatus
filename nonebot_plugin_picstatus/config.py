from typing import List, Optional, Set, Tuple

from nonebot import get_driver
from pydantic import BaseModel


class TestSiteCfg(BaseModel):
    name: str
    url: str
    use_proxy: bool = False


class Cfg(BaseModel):
    superusers: Set[str] = set()
    nickname: Set[str] = set()

    proxy: Optional[str] = None

    ps_only_su: bool = False
    ps_blur_radius: int = 4
    ps_font: Optional[str] = None
    ps_ignore_parts: List[str] = []
    ps_ignore_bad_parts: bool = False
    ps_ignore_disk_ios: List[str] = []
    ps_use_env_nick: bool = False
    ps_need_at: bool = False
    ps_mask_color: Tuple[int, int, int, int] = (255, 255, 255, 125)
    ps_bg_color: Tuple[int, int, int, int] = (255, 255, 255, 150)
    ps_ignore_nets: List[str] = ["^lo$", "^Loopback"]
    ps_ignore_no_io_disk: bool = False
    ps_ignore_0b_net: bool = False
    ps_custom_bg: List[str] = []
    ps_footer_size: int = 22
    ps_test_sites: List[TestSiteCfg] = [
        TestSiteCfg(name="百度", url="https://baidu.com"),
        TestSiteCfg(name="Google", url="https://google.com", use_proxy=True),
    ]
    ps_test_timeout: int = 5
    ps_max_text_len: int = 18


config: Cfg = Cfg.parse_obj(get_driver().config.dict())
