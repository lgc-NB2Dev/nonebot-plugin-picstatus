import asyncio
from pathlib import Path

import pytest

from tests_nbp_picstatus.utils.logging import LogRecorder
from tests_nbp_picstatus.utils.preloader import cancel_preloader_tasks


@pytest.mark.asyncio
async def test_skips_an_invalid_preload_entry_before_a_valid_candidate(
    picstatus_loaded: None,
    tmp_path: Path,
) -> None:
    """A broken cache entry does not hide a later usable preloaded background."""
    from nonebot_plugin_picstatus import bg_provider as bg

    preloader = bg.BgPreloader(0)
    missing = bg.BgFileData(tmp_path / "missing.webp", "image/webp")
    expected = bg.BgBytesData(b"usable", "image/webp")
    await preloader.background_queue.put(missing)
    await preloader.background_queue.put(expected)

    assert await preloader.get() == expected


@pytest.mark.asyncio
async def test_consumes_preloaded_backgrounds_in_fifo_order(
    picstatus_loaded: None,
) -> None:
    """Available preloaded backgrounds are returned in their insertion order."""
    from nonebot_plugin_picstatus import bg_provider as bg

    preloader = bg.BgPreloader(0)
    first = bg.BgBytesData(b"first", "image/webp")
    second = bg.BgBytesData(b"second", "image/webp")
    await preloader.background_queue.put(first)
    await preloader.background_queue.put(second)

    assert await preloader.get() == first
    assert await preloader.get() == second


@pytest.mark.asyncio
async def test_concurrent_cache_misses_start_independent_fire_retrievals(
    picstatus_loaded: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Concurrent cache misses each obtain a background without waiting for another."""
    from nonebot_plugin_picstatus import bg_provider as bg

    calls = 0
    monkeypatch.setattr(bg, "registered_bg_providers", {})

    @bg.bg_provider("direct")
    async def direct(num: int):
        nonlocal calls
        calls += 1
        yield bg.BgBytesData(str(calls).encode(), "image/webp")

    monkeypatch.setattr(bg.config, "ps_bg_provider", "direct")
    preloader = bg.BgPreloader(0)

    results = await asyncio.gather(preloader.get(), preloader.get())

    assert calls == 2
    assert {result.data for result in results} == {b"1", b"2"}


@pytest.mark.asyncio
async def test_retains_a_late_fire_retrieval_for_the_next_request(
    picstatus_loaded: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A fire retrieval that outlives its caller caches its later result."""
    from nonebot_plugin_picstatus import bg_provider as bg

    ready = asyncio.Event()
    release = asyncio.Event()
    expected = bg.BgBytesData(b"late", "image/webp")
    monkeypatch.setattr(bg, "registered_bg_providers", {})

    @bg.bg_provider("delayed")
    async def delayed(num: int):
        ready.set()
        await release.wait()
        yield expected

    monkeypatch.setattr(bg.config, "ps_bg_provider", "delayed")
    preloader = bg.BgPreloader(0)
    preloader.fire_return_timeout = 0
    first_request = asyncio.create_task(preloader.get())

    try:
        await ready.wait()
        await asyncio.wait_for(first_request, timeout=0.1)
        fire_task = next(iter(preloader.fire_tasks))
        release.set()
        await fire_task

        assert await preloader.get() == expected
    finally:
        release.set()
        await cancel_preloader_tasks(preloader)


@pytest.mark.asyncio
async def test_returns_the_first_fire_candidate_without_waiting_for_generator_end(
    picstatus_loaded: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A fire retrieval returns as soon as its provider yields the first candidate."""
    from nonebot_plugin_picstatus import bg_provider as bg

    first_candidate_ready = asyncio.Event()
    release = asyncio.Event()
    expected = bg.BgBytesData(b"first", "image/webp")
    monkeypatch.setattr(bg, "registered_bg_providers", {})

    @bg.bg_provider("slow_cleanup")
    async def slow_cleanup(num: int):
        first_candidate_ready.set()
        yield expected
        await release.wait()

    monkeypatch.setattr(bg.config, "ps_bg_provider", "slow_cleanup")
    preloader = bg.BgPreloader(0)
    request = asyncio.create_task(preloader.get())

    await first_candidate_ready.wait()
    try:
        assert await asyncio.wait_for(request, timeout=0.1) == expected
        await asyncio.sleep(0)
        assert not preloader.fire_tasks
    finally:
        release.set()
        await asyncio.gather(request, return_exceptions=True)


@pytest.mark.asyncio
async def test_stops_routine_preloading_after_the_retry_budget_is_exhausted(
    picstatus_loaded: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Three empty routine preload attempts suspend further background requests."""
    from nonebot_plugin_picstatus import bg_provider as bg

    attempts = 0
    third_attempt = asyncio.Event()
    fourth_attempt = asyncio.Event()
    never = asyncio.Event()
    logger = LogRecorder()
    monkeypatch.setattr(bg, "registered_bg_providers", {})
    monkeypatch.setattr(bg, "logger", logger)

    @bg.bg_provider("empty")
    async def empty(num: int):
        nonlocal attempts
        attempts += 1
        if attempts == 3:
            third_attempt.set()
        if attempts == 4:
            fourth_attempt.set()
            await never.wait()
        if False:
            yield bg.create_none_bg()

    monkeypatch.setattr(bg.config, "ps_bg_provider", "empty")
    preloader = bg.BgPreloader(1)
    preloader.start_preload()

    try:
        await third_attempt.wait()
        await asyncio.sleep(0)

        assert attempts == 3
        assert not fourth_attempt.is_set()
        assert len(logger.warning_messages) == 3
    finally:
        await cancel_preloader_tasks(preloader)


@pytest.mark.asyncio
async def test_a_later_get_resumes_preloading_after_retry_budget_exhaustion(
    picstatus_loaded: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Any later get resumes routine preloading after exhausted empty attempts."""
    from nonebot_plugin_picstatus import bg_provider as bg

    attempts = 0
    third_attempt = asyncio.Event()
    fourth_attempt = asyncio.Event()
    release_recovery = asyncio.Event()
    recovered = bg.BgBytesData(b"recovered", "image/webp")
    monkeypatch.setattr(bg, "registered_bg_providers", {})

    @bg.bg_provider("recovering")
    async def recovering(num: int):
        nonlocal attempts
        attempts += 1
        if attempts == 3:
            third_attempt.set()
        if attempts <= 3:
            if False:
                yield bg.create_none_bg()
            return
        fourth_attempt.set()
        await release_recovery.wait()
        yield recovered

    monkeypatch.setattr(bg.config, "ps_bg_provider", "recovering")
    preloader = bg.BgPreloader(1)
    preloader.start_preload()

    try:
        await third_attempt.wait()
        await asyncio.sleep(0)
        assert attempts == 3
        assert not fourth_attempt.is_set()

        cached = bg.BgBytesData(b"cached", "image/webp")
        await preloader.background_queue.put(cached)
        assert await preloader.get() == cached

        await fourth_attempt.wait()
        release_recovery.set()
        assert await preloader.get() == recovered
    finally:
        release_recovery.set()
        await cancel_preloader_tasks(preloader)


@pytest.mark.asyncio
async def test_logs_an_empty_fire_retrieval_as_a_warning(
    picstatus_loaded: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An empty fire retrieval uses the local fallback without an error-level log."""
    from nonebot_plugin_picstatus import bg_provider as bg

    logger = LogRecorder()
    monkeypatch.setattr(bg, "registered_bg_providers", {})

    @bg.bg_provider("empty")
    async def empty(num: int):
        if False:
            yield bg.create_none_bg()

    monkeypatch.setattr(bg, "logger", logger)
    monkeypatch.setattr(bg.config, "ps_bg_provider", "empty")
    preloader = bg.BgPreloader(0)

    assert (await preloader.get()).data is not None
    assert len(logger.warning_messages) == 1
    assert not logger.error_messages


@pytest.mark.asyncio
async def test_a_partial_preload_result_only_refills_the_remaining_gap(
    picstatus_loaded: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A partial result succeeds and requests only the missing preload candidate."""
    from nonebot_plugin_picstatus import bg_provider as bg

    requested_counts: list[int] = []
    second_request = asyncio.Event()
    monkeypatch.setattr(bg, "registered_bg_providers", {})

    @bg.bg_provider("partial")
    async def partial(num: int):
        requested_counts.append(num)
        if len(requested_counts) == 2:
            second_request.set()
        yield bg.BgBytesData(str(len(requested_counts)).encode(), "image/webp")

    monkeypatch.setattr(bg.config, "ps_bg_provider", "partial")
    preloader = bg.BgPreloader(2)
    preloader.start_preload()

    try:
        await second_request.wait()
        await asyncio.sleep(0)

        assert requested_counts == [2, 1]
        assert preloader.background_queue.qsize() == 2
    finally:
        await cancel_preloader_tasks(preloader)


@pytest.mark.asyncio
async def test_consuming_during_preloading_starts_a_follow_up_refill(
    picstatus_loaded: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A cache hit during routine loading is replenished after the active task ends."""
    from nonebot_plugin_picstatus import bg_provider as bg

    calls = 0
    first_candidate = asyncio.Event()
    release_first_request = asyncio.Event()
    follow_up_request = asyncio.Event()
    never = asyncio.Event()
    monkeypatch.setattr(bg, "registered_bg_providers", {})

    @bg.bg_provider("slow")
    async def slow(num: int):
        nonlocal calls
        calls += 1
        if calls == 1:
            yield bg.BgBytesData(b"first", "image/webp")
            first_candidate.set()
            await release_first_request.wait()
            yield bg.BgBytesData(b"second", "image/webp")
            return
        follow_up_request.set()
        await never.wait()
        if False:
            yield bg.create_none_bg()

    monkeypatch.setattr(bg.config, "ps_bg_provider", "slow")
    preloader = bg.BgPreloader(2)
    preloader.start_preload()

    try:
        await first_candidate.wait()
        assert await preloader.get() == bg.BgBytesData(b"first", "image/webp")

        release_first_request.set()
        await follow_up_request.wait()

        assert calls == 2
    finally:
        release_first_request.set()
        await cancel_preloader_tasks(preloader)


@pytest.mark.asyncio
async def test_provider_exceptions_consume_the_routine_retry_budget(
    picstatus_loaded: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Three routine provider exceptions exhaust the same retry budget as empty results."""
    from nonebot_plugin_picstatus import bg_provider as bg

    attempts = 0
    third_attempt = asyncio.Event()
    monkeypatch.setattr(bg, "registered_bg_providers", {})

    @bg.bg_provider("broken")
    async def broken(num: int):
        nonlocal attempts
        attempts += 1
        if attempts == 3:
            third_attempt.set()
        raise RuntimeError("broken provider")
        if False:
            yield bg.create_none_bg()

    monkeypatch.setattr(bg.config, "ps_bg_provider", "broken")
    preloader = bg.BgPreloader(1)
    preloader.start_preload()

    try:
        await asyncio.wait_for(third_attempt.wait(), timeout=0.1)
        assert attempts == 3
    finally:
        await cancel_preloader_tasks(preloader)


@pytest.mark.asyncio
async def test_cancels_a_fire_task_that_misses_its_deadline(
    picstatus_loaded: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A fire retrieval without a candidate is cancelled at its task deadline."""
    from nonebot_plugin_picstatus import bg_provider as bg

    started = asyncio.Event()
    cancelled = asyncio.Event()
    never = asyncio.Event()
    monkeypatch.setattr(bg, "registered_bg_providers", {})

    @bg.bg_provider("stalled")
    async def stalled(num: int):
        try:
            started.set()
            await never.wait()
            yield bg.create_none_bg()
        finally:
            cancelled.set()

    monkeypatch.setattr(bg.config, "ps_bg_provider", "stalled")
    preloader = bg.BgPreloader(0)
    preloader.fire_return_timeout = 0
    preloader.fire_task_timeout = 1
    request = asyncio.create_task(preloader.get())

    try:
        await started.wait()
        assert (await asyncio.wait_for(request, timeout=0.1)).data is not None
        await asyncio.wait_for(cancelled.wait(), timeout=1.1)
        await asyncio.sleep(0)
        assert not preloader.fire_tasks
    finally:
        never.set()
        await cancel_preloader_tasks(preloader)


@pytest.mark.asyncio
async def test_close_cancels_routine_and_fire_preloading(
    picstatus_loaded: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Closing a preloader cancels and waits for routine and fire retrieval tasks."""
    from nonebot_plugin_picstatus import bg_provider as bg

    routine_started = asyncio.Event()
    fire_started = asyncio.Event()
    cancelled = asyncio.Event()
    never = asyncio.Event()
    calls = 0
    active_tasks = 0
    monkeypatch.setattr(bg, "registered_bg_providers", {})

    @bg.bg_provider("stalled")
    async def stalled(num: int):
        nonlocal active_tasks, calls
        calls += 1
        active_tasks += 1
        if calls == 1:
            routine_started.set()
        else:
            fire_started.set()
        try:
            await never.wait()
            yield bg.create_none_bg()
        finally:
            active_tasks -= 1
            if active_tasks == 0:
                cancelled.set()

    monkeypatch.setattr(bg.config, "ps_bg_provider", "stalled")
    preloader = bg.BgPreloader(1)
    preloader.start_preload()
    request = asyncio.create_task(preloader.get())

    try:
        await routine_started.wait()
        await fire_started.wait()
        await preloader.close()

        assert preloader.current_load_task_main is None
        assert not preloader.fire_tasks
        await asyncio.wait_for(cancelled.wait(), timeout=0.1)
        assert (await asyncio.wait_for(request, timeout=0.1)).data is not None
    finally:
        never.set()
        await cancel_preloader_tasks(preloader)
