import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Dict, Generic, Set, TypeVar
from typing_extensions import Protocol

from nonebot import get_plugin_config, logger
from pydantic import BaseModel

from ..collectors import collect_all, registered_collectors
from ..config import config

TM = TypeVar("TM", bound=BaseModel, contravariant=True)


class TemplateRenderer(Generic[TM], Protocol):
    def __call__(self, collected: Dict[str, Any], config: TM) -> Awaitable[bytes]: ...


@dataclass()
class TemplateInfo:
    collectors: Set[str]
    config: BaseModel
    renderer: TemplateRenderer

    async def __call__(self):
        return await self.renderer(await collect_all(), self.config)


loaded_templates: Dict[str, TemplateInfo] = {}


def load_template(name: str):
    module = importlib.import_module(f".{name}", __package__)
    assert module

    if (not hasattr(module, "render")) or (not callable(module.render)):
        raise ValueError(f"Template {name} has wrong render function")
    if (not hasattr(module, "collecting")) or (
        (not isinstance(module.collecting, (list, tuple, set)))
        and (module.collecting != "all")
    ):
        raise ValueError(f"Template {name} has wrong collectors declared")
    if (not hasattr(module, "TemplateConfig")) or (
        not issubclass(module.TemplateConfig, BaseModel)
    ):
        raise ValueError(f"Template {name} has wrong TemplateConfig declared")
    template_info = TemplateInfo(
        collectors=set(
            registered_collectors if module.collecting == "all" else module.collecting,
        ),
        config=get_plugin_config(module.TemplateConfig),
        renderer=module.render,
    )
    loaded_templates[name] = template_info
    logger.debug(f"Loaded template {name} {template_info}")
    return template_info


def load_templates():
    for module in Path(__file__).parent.iterdir():
        name = module.name
        if (not module.is_dir()) or name.startswith("_"):
            continue
        load_template(name)


async def render_current_template():
    return await loaded_templates[config.ps_template]()
