from nonebot import get_driver
from pydantic import BaseModel


class Cfg(BaseModel):
    superusers: set[str] = set()

    ps_only_su: bool = False
    ps_blur_radius: int = 4
    ps_font: str = None


config: Cfg = Cfg.parse_obj(get_driver().config.dict())
