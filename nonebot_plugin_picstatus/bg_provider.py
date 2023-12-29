import random
from pathlib import Path
from typing import Awaitable, Callable, Dict, List, TypeVar

import anyio
from httpx import AsyncClient
from nonebot import logger

from .config import DEFAULT_BG_PATH, config

BGProviderType = Callable[[], Awaitable[bytes]]
TBP = TypeVar("TBP", bound=BGProviderType)

registered_bg_providers: Dict[str, BGProviderType] = {}


def get_bg_files() -> List[Path]:
    if not config.ps_bg_local_path.exists():
        logger.warning("Custom background path does not exist, fallback to default")
        return [DEFAULT_BG_PATH]
    if config.ps_bg_local_path.is_file():
        return [config.ps_bg_local_path]

    files = [x for x in config.ps_bg_local_path.glob("*") if x.is_file()]
    if not files:
        logger.warning("Custom background dir has no file in it, fallback to default")
        return [DEFAULT_BG_PATH]
    return files


BG_FILES = get_bg_files()


def bg_provider(func: TBP) -> TBP:
    name = func.__name__
    if name in registered_bg_providers:
        raise ValueError(f"Duplicate bg provider name `{name}`")
    registered_bg_providers[name] = func
    return func


@bg_provider
async def gm():
    async with AsyncClient(
        follow_redirects=True,
        proxies=config.proxy,
        timeout=config.ps_req_timeout,
    ) as cli:
        url = (
            (await cli.get("https://api.gumengya.com/Api/DmImg"))
            .raise_for_status()
            .json()["data"]["url"]
        )
        return (await cli.get(url)).raise_for_status().content


@bg_provider
async def loli():
    async with AsyncClient(
        follow_redirects=True,
        proxies=config.proxy,
        timeout=config.ps_req_timeout,
    ) as cli:
        return (
            (await cli.get("https://www.loliapi.com/acg/pe/"))
            .raise_for_status()
            .content
        )


@bg_provider
async def lolicon():
    async with AsyncClient(
        follow_redirects=True,
        proxies=config.proxy,
        timeout=config.ps_req_timeout,
    ) as cli:
        resp = await cli.get(
            "https://api.lolicon.app/setu/v2",
            params={
                "r18": config.ps_bg_lolicon_r18_type,
                "proxy": "false",
                "excludeAI": "true",
            },
        )
        url = resp.raise_for_status().json()["data"][0]["urls"]["original"]
        resp = await cli.get(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/119.0.0.0 "
                    "Safari/537.36"
                ),
                "Referer": "https://www.pixiv.net/",
            },
        )
        return resp.raise_for_status().content


@bg_provider
async def local():
    file = random.choice(BG_FILES)
    logger.debug(f"Choice background file `{file}`")
    return await anyio.Path(file).read_bytes()


@bg_provider
async def none():
    return b""


async def get_bg():
    if config.ps_bg_provider in registered_bg_providers:
        try:
            return await registered_bg_providers[config.ps_bg_provider]()
        except Exception:
            logger.exception("Error when getting background, fallback to local")
    else:
        logger.warning(
            f"Unknown background provider `{config.ps_bg_provider}`, fallback to local",
        )
    return await local()
