def _import():
    from pathlib import Path

    from cookit import auto_import

    auto_import(Path(__file__).parent, __package__)


_import()
del _import
