import asyncio

import pytest

from tests_nbp_picstatus.utils.logging import LogRecorder
from tests_nbp_picstatus.utils.preloader import cancel_preloader_tasks


@pytest.mark.asyncio
async def test_no_preload_provider_skips_routine_preloading(
    picstatus_loaded: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An explicitly selected no-preload provider receives no routine preload call."""
    from nonebot_plugin_picstatus import bg_provider as bg

    calls = 0
    monkeypatch.setattr(bg, "registered_bg_providers", {})

    @bg.bg_provider("on_demand", no_preload=True)
    async def on_demand(num: int):
        nonlocal calls
        calls += 1
        yield bg.BgBytesData(b"image", "image/webp")

    monkeypatch.setattr(bg.config, "ps_bg_provider", "on_demand")
    preloader = bg.BgPreloader(1)
    preloader.start_preload()

    try:
        await asyncio.sleep(0)
        await asyncio.sleep(0)

        assert calls == 0
    finally:
        await cancel_preloader_tasks(preloader)


@pytest.mark.asyncio
async def test_no_preload_provider_still_serves_a_fire_retrieval(
    picstatus_loaded: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No-preload eligibility does not prevent a cache miss from fetching one image."""
    from nonebot_plugin_picstatus import bg_provider as bg

    calls = 0
    expected = bg.BgBytesData(b"image", "image/webp")
    monkeypatch.setattr(bg, "registered_bg_providers", {})

    @bg.bg_provider("on_demand", no_preload=True)
    async def on_demand(num: int):
        nonlocal calls
        calls += 1
        yield expected

    monkeypatch.setattr(bg.config, "ps_bg_provider", "on_demand")
    preloader = bg.BgPreloader(1)

    try:
        assert await preloader.get() == expected
        assert calls == 1
    finally:
        await cancel_preloader_tasks(preloader)


@pytest.mark.asyncio
async def test_logs_an_unknown_provider_as_an_error(
    picstatus_loaded: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An unknown configured provider is visible as an error before local fallback."""
    from nonebot_plugin_picstatus import bg_provider as bg

    logger = LogRecorder()
    monkeypatch.setattr(bg, "registered_bg_providers", {})
    monkeypatch.setattr(bg, "logger", logger)
    monkeypatch.setattr(bg.config, "ps_bg_provider", "missing")

    candidates = [candidate async for candidate in bg.fetch_bg(1)]

    assert len(candidates) == 1
    assert len(logger.error_messages) == 1
    assert not logger.warning_messages


@pytest.mark.asyncio
async def test_a_fallback_candidate_does_not_disable_routine_preloading(
    picstatus_loaded: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fallback to a no-preload source does not change the configured source policy."""
    from nonebot_plugin_picstatus import bg_provider as bg

    monkeypatch.setattr(bg.config, "ps_bg_provider", "missing")
    preloader = bg.BgPreloader(1)
    preloader.start_preload()

    try:
        await asyncio.sleep(0)
        await asyncio.sleep(0)

        assert preloader.background_queue.qsize() == 1
    finally:
        await cancel_preloader_tasks(preloader)


@pytest.mark.asyncio
async def test_logs_provider_exceptions_as_warning_with_a_debug_stack(
    picstatus_loaded: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A provider exception falls back for this request and records the failure reason."""
    from nonebot_plugin_picstatus import bg_provider as bg

    exceptions: list[tuple[BaseException, str]] = []
    monkeypatch.setattr(bg, "registered_bg_providers", {})

    @bg.bg_provider("broken")
    async def broken(num: int):
        raise RuntimeError("broken provider")
        if False:
            yield bg.create_none_bg()

    monkeypatch.setattr(
        bg,
        "log_exception_warning",
        lambda exception, message: exceptions.append((exception, message)),
    )
    monkeypatch.setattr(bg.config, "ps_bg_provider", "broken")
    candidates = [candidate async for candidate in bg.fetch_bg(1)]

    assert len(candidates) == 1
    assert len(exceptions) == 1
    assert isinstance(exceptions[0][0], RuntimeError)
