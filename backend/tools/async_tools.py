import asyncio
from functools import wraps
from typing import Callable, Any


def run_async_function(async_func, *args, **kwargs):
    # Used to test async functions in django shell

    loop = asyncio.get_event_loop()
    if loop.is_running():
        # If there's already a running event loop, create a new one
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        result = new_loop.run_until_complete(async_func(*args, **kwargs))
        asyncio.set_event_loop(loop)  # Restore the original loop
    else:
        result = loop.run_until_complete(async_func(*args, **kwargs))
    return result
