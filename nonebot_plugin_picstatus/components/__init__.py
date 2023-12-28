import importlib
from pathlib import Path
from typing import Awaitable, Callable, Dict, TypeVar

ComponentType = Callable[[], Awaitable[str]]
TC = TypeVar("TC", bound=ComponentType)

components: Dict[str, ComponentType] = {}


def register_component(component: TC) -> TC:
    name = component.__name__
    if name in components:
        raise ValueError(f"Duplicate component name `{name}`")
    components[name] = component
    return component


def load_components():
    for module in Path(__file__).parent.iterdir():
        if module.name.startswith("_"):
            continue
        importlib.import_module(f".{module.stem}", __package__)
