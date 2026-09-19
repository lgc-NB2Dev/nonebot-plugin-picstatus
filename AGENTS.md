# AGENTS.md

First: This project expects the working root to be github repo `lgc-NB2Dev/workspace` because some recommended workspace-level files is not stored in this plugin project. If you are not working from that root, stop and notify the user.

## Commands

NOTE: The following command are expected to be run under the plugin repo root rather than the workspace root.

```bash
poe test [...]      # pytest
poe coverage [...]  # pytest (with branch coverage and terminal report)
```

## Structure

```text
nonebot_plugin_picstatus/  PicStatus plugin package
  __init__.py              Plugin entry, metadata and startup wiring
  __main__.py              The picstatus command matcher
  config.py                Config model, resource paths and cache dirs
  bg_provider.py           Background provider registry, builtins, preloader
  misc_statistics.py       Bot caches and runtime counters
  util.py                  Shared formatting and HTTP helpers
  collectors/              One module per collected status subject
    __init__.py            Collector base classes, decorators and registries
    cpu.py                 CPU usage and frequency
    mem.py                 Memory usage
    disk.py                Disk usage
    network.py             Network IO and site reachability
    process.py             Top processes by CPU and memory
    bot.py                 Bot info and message counters
    misc.py                Host, OS and runtime facts
  templates/               Template registry and render dispatch
    __init__.py            Template registry, loader and decorator
    pw_render.py           Playwright renderer and resource routing
    default/               Built-in default template
      __init__.py          Default template renderer
      res/
        css/               Stylesheets
        templates/         Jinja2 page templates
  res/
    assets/                Default background and avatar images
    js/                    Browser scripts injected into rendered pages
tests_nbp_picstatus/       Pytest suite mirroring the plugin package; shared scaffolding in utils/
examples/
  external_example/        Example external provider, collector and template
docs/
  adr/                     Architecture decision records
.github/workflows/         CI test and PyPI publish workflows
CONTEXT.md                 Background selection domain glossary
.env.example               Example NoneBot environment configuration
```

## Rules

Currently empty

## Gotchas

Currently empty
