import asyncio
from pathlib import Path

import pytest

from tests_nbp_picstatus.utils.preloader import cancel_preloader_tasks


@pytest.mark.asyncio
async def test_returns_every_available_file_when_fewer_exist_than_requested(
    picstatus_loaded: None,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A local request larger than the file set yields all files instead of failing."""
    from nonebot_plugin_picstatus import bg_provider as bg

    only = tmp_path / "only.webp"
    only.write_bytes(b"only")
    monkeypatch.setattr(bg, "BG_FILES", [only])
    monkeypatch.setattr(bg.config, "ps_bg_provider", "local")

    candidates = [x async for x in bg.fetch_bg(2, fallback_on_error=False)]

    assert candidates == [bg.BgFileData(only, "image/webp")]


@pytest.mark.asyncio
async def test_unknown_provider_fallback_returns_every_available_file(
    picstatus_loaded: None,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The unknown-provider fallback also yields all files when the set is smaller."""
    from nonebot_plugin_picstatus import bg_provider as bg

    only = tmp_path / "only.webp"
    only.write_bytes(b"only")
    monkeypatch.setattr(bg, "BG_FILES", [only])
    monkeypatch.setattr(bg, "registered_bg_providers", {})
    monkeypatch.setattr(bg.config, "ps_bg_provider", "missing")

    candidates = [x async for x in bg.fetch_bg(2)]

    assert candidates == [bg.BgFileData(only, "image/webp")]


@pytest.mark.asyncio
async def test_skips_routine_preloading(
    picstatus_loaded: None,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Local files are never fetched ahead of a request."""
    from nonebot_plugin_picstatus import bg_provider as bg

    only = tmp_path / "only.webp"
    only.write_bytes(b"local bytes")
    cache_dir = tmp_path / "cache"
    monkeypatch.setattr(bg, "BG_FILES", [only])
    monkeypatch.setattr(bg, "BG_PRELOAD_CACHE_DIR", cache_dir)
    monkeypatch.setattr(bg.config, "ps_bg_provider", "local")
    preloader = bg.BgPreloader(1)
    preloader.start_preload()

    try:
        await asyncio.sleep(0)
        await asyncio.sleep(0)

        assert preloader.background_queue.qsize() == 0
        assert not cache_dir.exists()
    finally:
        await cancel_preloader_tasks(preloader)


@pytest.mark.asyncio
async def test_still_serves_a_cache_miss(
    picstatus_loaded: None,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Skipping routine preloading does not stop a request from reading a local file."""
    from nonebot_plugin_picstatus import bg_provider as bg

    only = tmp_path / "only.webp"
    only.write_bytes(b"local bytes")
    monkeypatch.setattr(bg, "BG_FILES", [only])
    monkeypatch.setattr(bg.config, "ps_bg_provider", "local")

    preloader = bg.BgPreloader(0)

    try:
        assert await preloader.get() == bg.BgBytesData(b"local bytes", "image/webp")
    finally:
        await cancel_preloader_tasks(preloader)
