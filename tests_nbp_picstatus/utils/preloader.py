import asyncio
from typing import Any


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
