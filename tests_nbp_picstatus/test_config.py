import pytest
from pydantic import ValidationError


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


def test_defaults_fire_retrieval_timeouts(picstatus_loaded: None) -> None:
    """Fire retrievals have separate return-gate and task-deadline defaults."""
    from nonebot_plugin_picstatus.config import ConfigModel

    config = ConfigModel(superusers=set(), nickname=set())

    assert config.ps_bg_fire_return_timeout == 15
    assert config.ps_bg_fire_task_timeout == 60


@pytest.mark.parametrize(
    ("return_timeout", "task_timeout"),
    [
        (0, 60),
        (15, 0),
        (61, 60),
        (15, 14),
    ],
)
def test_rejects_invalid_fire_retrieval_timeouts(
    picstatus_loaded: None,
    return_timeout: int,
    task_timeout: int,
) -> None:
    """Fire timeouts must be positive and the task deadline cannot precede its gate."""
    from nonebot_plugin_picstatus.config import ConfigModel

    with pytest.raises(ValidationError):
        ConfigModel(
            superusers=set(),
            nickname=set(),
            ps_bg_fire_return_timeout=return_timeout,
            ps_bg_fire_task_timeout=task_timeout,
        )


def test_requires_a_url_for_the_url_provider(picstatus_loaded: None) -> None:
    """The URL provider is rejected before any background request is made."""
    from nonebot_plugin_picstatus.config import ConfigModel

    with pytest.raises(ValueError, match="PS_BG_URL"):
        ConfigModel(superusers=set(), nickname=set(), ps_bg_provider="url")
