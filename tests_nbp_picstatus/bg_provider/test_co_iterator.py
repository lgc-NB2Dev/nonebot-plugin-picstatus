import asyncio
import gc
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from typing_extensions import Protocol

    class Pacer(Protocol):
        """Typed view of the test iterator's observability hooks."""

        runs: int
        active: int

        def __aiter__(self) -> AsyncIterator[int]: ...


def build_iterator(
    num: int,
    *,
    fail_after: int | None = None,
) -> "Pacer":
    """Build an iterator that paces `num` candidates with real await points.

    When `fail_after` is set, the producer raises after emitting that index.
    """
    from nonebot_plugin_picstatus.bg_provider import CoIterator

    class CountingIterator(CoIterator[int]):
        def __init__(self) -> None:
            super().__init__()
            self.runs = 0
            self.active = 0

        async def run_tasks(self, queue: "asyncio.Queue[int | None]") -> None:
            self.runs += 1
            self.active += 1
            try:
                for i in range(num):
                    await asyncio.sleep(0.001)
                    if i == fail_after:
                        raise RuntimeError("producer failed")
                    await queue.put(i)
            finally:
                self.active -= 1

    return CountingIterator()


@pytest.mark.asyncio
async def test_concurrent_iterations_of_one_instance_stay_independent(
    picstatus_loaded: None,
) -> None:
    """Each concurrent iteration of one provider receives a complete stream."""
    iterator = build_iterator(3)

    async def consume() -> list[int]:
        return [x async for x in iterator]

    first, second = await asyncio.gather(consume(), consume())

    assert sorted(first) == [0, 1, 2]
    assert sorted(second) == [0, 1, 2]


@pytest.mark.asyncio
async def test_reiterating_one_instance_starts_a_fresh_stream(
    picstatus_loaded: None,
) -> None:
    """A second iteration of the same provider yields a full new stream."""
    iterator = build_iterator(2)

    assert [x async for x in iterator] == [0, 1]
    assert [x async for x in iterator] == [0, 1]


@pytest.mark.asyncio
async def test_a_producer_error_reaches_its_consumer_unchanged(
    picstatus_loaded: None,
) -> None:
    """A failing producer surfaces its own exception rather than a task-group wrapper."""
    iterator = build_iterator(1, fail_after=0)

    with pytest.raises(RuntimeError, match="producer failed"):
        _ = [x async for x in iterator]


@pytest.mark.asyncio
async def test_abandoning_an_iteration_stops_its_producer_quietly(
    picstatus_loaded: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An abandoned iteration cancels its producer without reporting a stray error."""
    iterator = build_iterator(5)
    reported: list[Any] = []
    loop = asyncio.get_running_loop()
    monkeypatch.setattr(loop, "call_exception_handler", reported.append)

    stream: AsyncIterator[int] = iterator.__aiter__()
    async for _ in stream:
        break
    del stream
    gc.collect()
    for _ in range(3):
        await asyncio.sleep(0)

    assert iterator.active == 0
    assert reported == []


@pytest.mark.asyncio
async def test_abandoning_after_a_producer_error_stays_quiet(
    picstatus_loaded: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Abandoning an iteration whose producer already failed reports nothing."""
    iterator = build_iterator(5, fail_after=1)
    reported: list[Any] = []
    loop = asyncio.get_running_loop()
    monkeypatch.setattr(loop, "call_exception_handler", reported.append)

    stream: AsyncIterator[int] = iterator.__aiter__()
    assert await stream.__anext__() == 0
    await asyncio.sleep(0.05)  # let the producer fail before the stream is abandoned
    del stream
    gc.collect()
    for _ in range(3):
        await asyncio.sleep(0)

    assert iterator.active == 0
    assert reported == []
