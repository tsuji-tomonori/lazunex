from __future__ import annotations

from collections.abc import Awaitable, Callable


def record_async_call(calls: list[str], name: str) -> Callable[..., Awaitable[None]]:
    async def stub(*args: object) -> None:
        _ = args
        calls.append(name)

    return stub
