# ruff: noqa: ARG001

import asyncio
from pathlib import Path
from typing import Any
from typing_extensions import Self

import pytest
from pydantic import ValidationError


class LogRecorder:
    """Record logger calls made at the background-provider boundary."""

    def __init__(self) -> None:
        self.debug_messages: list[str] = []
        self.warning_messages: list[str] = []
        self.error_messages: list[str] = []
        self.exception_messages: list[str] = []

    def debug(self, message: str) -> None:
        self.debug_messages.append(message)

    def warning(self, message: str) -> None:
        self.warning_messages.append(message)

    def error(self, message: str) -> None:
        self.error_messages.append(message)

    def exception(self, message: str) -> None:
        self.exception_messages.append(message)

    def opt(self, **_: Any) -> Self:
        return self


async def cancel_preloader_tasks(preloader: Any) -> None:
    """Cancel all background tasks created by a preloader during a test."""
    tasks = {
        task
        for task in (*preloader.fire_tasks, preloader.current_load_task_main)
        if task is not None and not task.done()
    }
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)


@pytest.mark.parametrize(
    ("count", "expected"),
    [
        (1, [1]),
        (20, [20]),
        (21, [20, 1]),
        (40, [20, 20]),
    ],
)
def test_splits_requests_at_the_provider_limit(
    picstatus_loaded: None,
    count: int,
    expected: list[int],
) -> None:
    """A request is divided into full provider batches followed by its remainder."""
    from nonebot_plugin_picstatus import bg_provider as bg

    assert list(bg.iter_batch_sizes(count, 20)) == expected


@pytest.mark.parametrize("count", [0, -1])
def test_rejects_non_positive_provider_batch_size(
    picstatus_loaded: None,
    count: int,
) -> None:
    """A provider batch request must ask for at least one image."""
    from nonebot_plugin_picstatus import bg_provider as bg

    with pytest.raises(ValueError, match="positive"):
        list(bg.iter_batch_sizes(count, 20))


def test_rejects_a_negative_preload_target(picstatus_loaded: None) -> None:
    """The preload target cannot be negative."""
    from nonebot_plugin_picstatus.config import ConfigModel

    with pytest.raises(ValidationError):
        ConfigModel(superusers=set(), nickname=set(), ps_bg_preload_count=-1)


def test_defaults_the_preload_retry_limit_to_three(picstatus_loaded: None) -> None:
    """Routine preload recovery has a bounded default retry budget."""
    from nonebot_plugin_picstatus.config import ConfigModel

    config = ConfigModel(superusers=set(), nickname=set())

    assert config.ps_bg_preload_retry_limit == 3


def test_requires_a_url_for_the_url_provider(picstatus_loaded: None) -> None:
    """The URL provider is rejected before any background request is made."""
    from nonebot_plugin_picstatus.config import ConfigModel

    with pytest.raises(ValueError, match="PS_BG_URL"):
        ConfigModel(superusers=set(), nickname=set(), ps_bg_provider="url")


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


def test_consuming_a_plugin_cache_file_removes_it(
    picstatus_loaded: None,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A plugin-owned cached image is removed after its bytes are returned."""
    from nonebot_plugin_picstatus import bg_provider as bg

    monkeypatch.setattr(bg, "BG_PRELOAD_CACHE_DIR", tmp_path)
    expected = bg.BgBytesData(b"cached", "image/webp")

    cached = bg.cache_bg(expected)

    assert cached.path is not None
    assert cached.path.exists()
    assert bg.read_cached_bg_file(cached) == expected
    assert not cached.path.exists()


def test_consuming_a_local_background_keeps_its_file(
    picstatus_loaded: None,
    tmp_path: Path,
) -> None:
    """A user-owned local background remains after it is read."""
    from nonebot_plugin_picstatus import bg_provider as bg

    path = tmp_path / "local.webp"
    path.write_bytes(b"local")
    local = bg.BgFileData(path, "image/webp")

    assert bg.read_cached_bg_file(local) == bg.BgBytesData(b"local", "image/webp")
    assert path.exists()


def test_represents_an_intentional_empty_background_without_a_file(
    picstatus_loaded: None,
) -> None:
    """An empty background is a valid candidate rather than a cache read failure."""
    from nonebot_plugin_picstatus import bg_provider as bg

    empty = bg.BgBytesData(None, "application/octet-stream")

    assert bg.read_cached_bg_file(bg.cache_bg(empty)) == empty


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

    original_sleep = asyncio.sleep
    ready = asyncio.Event()
    release = asyncio.Event()
    expected = bg.BgBytesData(b"late", "image/webp")
    monkeypatch.setattr(bg, "registered_bg_providers", {})

    async def immediate_sleep(_: float) -> None:
        return None

    @bg.bg_provider("delayed")
    async def delayed(num: int):
        ready.set()
        await release.wait()
        yield expected

    monkeypatch.setattr(bg.aio, "sleep", immediate_sleep)
    monkeypatch.setattr(bg.config, "ps_bg_provider", "delayed")
    preloader = bg.BgPreloader(0)
    first_request = asyncio.create_task(preloader.get())

    try:
        await ready.wait()
        await first_request
        fire_task = next(iter(preloader.fire_tasks))
        release.set()
        await fire_task
        await original_sleep(0)

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
