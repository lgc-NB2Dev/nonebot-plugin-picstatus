import os
import platform
import time
from pathlib import Path
from typing import Dict, Optional, Tuple, Union

import nonebot

from ..render import ENVIRONMENT
from . import register_component


def parse_env(env: str) -> Dict[str, Optional[str]]:
    env_lines = env.strip().splitlines()
    env_dict: Dict[str, Optional[str]] = {}

    for line in env_lines:
        if "=" not in line:
            env_dict[line.upper()] = None
            continue

        key, value = line.split("=", 1)
        env_dict[key.upper()] = value.strip("\"'").strip()

    return env_dict


def parse_env_file(env_file: Union[str, Path]) -> Optional[Dict[str, Optional[str]]]:
    if not isinstance(env_file, Path):
        env_file = Path(env_file)
    if not env_file.exists():
        return None
    content = env_file.read_text(encoding="u8")
    return parse_env(content)


# Thanks to https://github.com/nonedesktop/nonebot-plugin-guestool/blob/main/nonebot_plugin_guestool/info.py
def get_linux_name_version() -> Optional[Tuple[str, str]]:
    env = parse_env_file("/etc/os-release")
    if env and (name := env.get("NAME")) and (version_id := env.get("VERSION_ID")):
        return name, version_id

    env = parse_env_file("/etc/lsb-release")
    if (
        env
        and (name := env.get("DISTRIB_ID"))
        and (version_id := env.get("DISTRIB_RELEASE"))
    ):
        return name, version_id

    return None


async def get_system_name():
    system, _, release, version, machine, _ = platform.uname()
    system, release, version = platform.system_alias(system, release, version)

    if system == "Java":
        _, _, _, (system, release, machine) = platform.java_ver()

    if system == "Darwin":
        return f"MacOS {platform.mac_ver()[0]} {machine}"

    if system == "Windows":
        return f"Windows {release} {platform.win32_edition()} {machine}"

    if system == "Linux":
        if (pfx := os.getenv("PREFIX")) and "termux" in pfx:
            system = f"Termux (Android) {release}"  # a strange platform

        elif os.getenv("ANDROID_ROOT") == "/system":
            system = f"Linux (Android) {release}"

        elif ver := get_linux_name_version():
            name, version_id = ver
            version = release if version_id.lower() == "rolling" else version_id
            system = f"{name} {version}"

        else:
            system = f"未知 Linux {release}"

        return f"{system} {machine}"

    return f"{system} {release}"


@register_component
async def footer():
    from .. import __version__

    txt = (
        f"NoneBot {nonebot.__version__} × PicStatus {__version__} | "
        f"{time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"{platform.python_implementation()} {platform.python_version()} | "
        f"{await get_system_name()}"
    )
    return await ENVIRONMENT.get_template("footer.html.jinja").render_async(footer=txt)
