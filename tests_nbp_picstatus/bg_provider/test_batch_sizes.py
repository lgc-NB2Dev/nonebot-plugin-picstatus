import pytest


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
