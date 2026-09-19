from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pytest


def test_consuming_a_plugin_cache_file_removes_it(
    picstatus_loaded: None,
    monkeypatch: "pytest.MonkeyPatch",
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
