import os
import platform
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple, Union

import nonebot
import psutil

from ..statistics import nonebot_run_time
from ..util import format_time_delta_ps
from . import first_time_collector, normal_collector, periodic_collector


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


@normal_collector("nonebot_run_time")
async def nonebot_run_time_str() -> str:
    now_time = datetime.now().astimezone()
    return (
        format_time_delta_ps(now_time - nonebot_run_time)
        if nonebot_run_time
        else "未知"
    )


@normal_collector()
async def system_run_time() -> str:
    now_time = datetime.now().astimezone()
    return format_time_delta_ps(
        now_time - datetime.fromtimestamp(psutil.boot_time()).astimezone(),
    )


@first_time_collector()
async def nonebot_version() -> str:
    return nonebot.__version__


@first_time_collector()
async def ps_version() -> str:
    from .. import __version__

    return __version__


@periodic_collector("time")
async def time_str() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


@first_time_collector()
async def python_version() -> str:
    return f"{platform.python_implementation()} {platform.python_version()}"


@first_time_collector()
async def system_name():
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
