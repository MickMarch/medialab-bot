"""Bounded retry with exponential backoff around the Discord login.

A host resolver blip at startup used to raise straight out of ``bot.start()``,
exit the process, and leave ``restart: unless-stopped`` crash-looping the
container every few seconds. Transient connection failures are retried here
with a capped exponential backoff and a clear log line saying what is being
waited on; anything that is not a connection problem (a bad token, a bug)
propagates immediately.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

import aiohttp

logger = logging.getLogger(__name__)

RETRYABLE_ERRORS: tuple[type[BaseException], ...] = (aiohttp.ClientConnectorError,)
"""Failures worth waiting out: DNS resolution and TCP connect errors."""

_BACKOFF_FACTOR = 2.0


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int
    base_delay_seconds: float
    max_delay_seconds: float

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if self.base_delay_seconds <= 0:
            raise ValueError("base_delay_seconds must be positive")
        if self.max_delay_seconds < self.base_delay_seconds:
            raise ValueError("max_delay_seconds must be at least base_delay_seconds")

    def delay_before(self, attempt: int) -> float:
        """Delay before retry number ``attempt`` (1-based)."""
        return min(
            self.base_delay_seconds * _BACKOFF_FACTOR ** (attempt - 1), self.max_delay_seconds
        )


async def start_with_retry(
    start: Callable[[], Awaitable[None]],
    policy: RetryPolicy,
    *,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> None:
    """Run ``start`` until it returns, retrying only ``RETRYABLE_ERRORS``.

    Re-raises the last connection error once ``policy.max_attempts`` is
    exhausted so the process still exits non-zero and the restart policy takes
    over from there.
    """
    for attempt in range(1, policy.max_attempts + 1):
        try:
            await start()
            return
        except RETRYABLE_ERRORS as exc:
            if attempt == policy.max_attempts:
                logger.error("Discord login failed after %d attempts; giving up: %s", attempt, exc)
                raise
            delay = policy.delay_before(attempt)
            logger.warning(
                "Discord login attempt %d/%d failed (%s); retrying in %.0fs",
                attempt,
                policy.max_attempts,
                exc,
                delay,
            )
            await sleep(delay)
