from typing import Set, Tuple

from nonebot import get_driver
from pydantic import BaseModel


class Cfg(BaseModel):
    superusers: Set[str] = set()
    nickname: Set[str] = set()

    ps_only_su: bool = False
    ps_blur_radius: int = 4
    ps_font: str = None
    ps_ignore_parts: Set[str] = set()
    ps_ignore_bad_parts: bool = False
    ps_use_env_nick: bool = False
    ps_need_at: bool = False
    ps_mask_color: Tuple[int, int, int, int] = (255, 255, 255, 125)
    ps_bg_color: Tuple[int, int, int, int] = (255, 255, 255, 150)
    ps_ignore_nets: Set[str] = set()


config: Cfg = Cfg.parse_obj(get_driver().config.dict())
