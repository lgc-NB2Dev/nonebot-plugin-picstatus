import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Dict, Optional, Set, TypedDict
from typing_extensions import Protocol, Unpack

from nonebot import logger

from ..bg_provider import BgData
from ..config import config


class TemplateRendererKwargs(TypedDict):
    collected: Dict[str, Any]
    bg: BgData


class TemplateRenderer(Protocol):
    __name__: str

    def __call__(
        self,
        **kwargs: Unpack[TemplateRendererKwargs],
    ) -> Awaitable[bytes]: ...


@dataclass()
class TemplateInfo:
    renderer: TemplateRenderer
    collectors: Optional[Set[str]] = None


loaded_templates: Dict[str, TemplateInfo] = {}


def pic_template(
    name: Optional[str] = None,
    collecting: Optional[Set[str]] = None,
):
    def deco(func: TemplateRenderer):
        template_name = name or func.__name__
        if template_name in loaded_templates:
            raise ValueError(f"Template {template_name} already exists")
        loaded_templates[template_name] = TemplateInfo(
            renderer=func,
            collectors=collecting,
        )
        logger.debug(f"Registered template {template_name}")

    return deco


def load_builtin_templates():
    for module in Path(__file__).parent.iterdir():
        name = module.name
        if (not module.is_dir()) or name.startswith("_"):
            continue
        assert importlib.import_module(f".{name}", __package__)


async def render_current_template(**kwargs: Unpack[TemplateRendererKwargs]):
    return await loaded_templates[config.ps_template].renderer(**kwargs)
