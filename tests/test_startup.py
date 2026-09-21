"""Login retry: transient connection failures back off and retry; anything else
propagates at once; a bounded number of attempts before giving up."""

from unittest.mock import AsyncMock

import aiohttp
import pytest
from discord.errors import LoginFailure

from medialab_bot.startup import RetryPolicy, start_with_retry

POLICY = RetryPolicy(max_attempts=4, base_delay_seconds=1.0, max_delay_seconds=5.0)


def _dns_error() -> aiohttp.ClientConnectorError:
    key = aiohttp.client_reqrep.ConnectionKey("discord.com", 443, True, True, None, None, None)
    return aiohttp.ClientConnectorDNSError(key, OSError("Temporary failure in name resolution"))


async def test_returns_after_first_success_without_sleeping() -> None:
    start = AsyncMock()
    sleep = AsyncMock()
    await start_with_retry(start, POLICY, sleep=sleep)
    assert start.await_count == 1
    sleep.assert_not_awaited()


async def test_retries_connection_errors_with_exponential_backoff() -> None:
    start = AsyncMock(side_effect=[_dns_error(), _dns_error(), None])
    sleep = AsyncMock()
    await start_with_retry(start, POLICY, sleep=sleep)
    assert start.await_count == 3
    assert [c.args[0] for c in sleep.await_args_list] == [1.0, 2.0]


async def test_backoff_is_capped_at_max_delay() -> None:
    start = AsyncMock(side_effect=[_dns_error(), _dns_error(), _dns_error(), None])
    sleep = AsyncMock()
    await start_with_retry(start, POLICY, sleep=sleep)
    assert [c.args[0] for c in sleep.await_args_list] == [1.0, 2.0, 4.0]
    policy = RetryPolicy(max_attempts=5, base_delay_seconds=3.0, max_delay_seconds=5.0)
    start = AsyncMock(side_effect=[_dns_error(), _dns_error(), _dns_error(), None])
    sleep = AsyncMock()
    await start_with_retry(start, policy, sleep=sleep)
    assert [c.args[0] for c in sleep.await_args_list] == [3.0, 5.0, 5.0]


async def test_gives_up_after_max_attempts_and_reraises_last_error() -> None:
    start = AsyncMock(side_effect=_dns_error())
    sleep = AsyncMock()
    with pytest.raises(aiohttp.ClientConnectorError):
        await start_with_retry(start, POLICY, sleep=sleep)
    assert start.await_count == POLICY.max_attempts
    assert sleep.await_count == POLICY.max_attempts - 1


async def test_does_not_retry_a_bad_token() -> None:
    start = AsyncMock(side_effect=LoginFailure("Improper token has been passed."))
    sleep = AsyncMock()
    with pytest.raises(LoginFailure):
        await start_with_retry(start, POLICY, sleep=sleep)
    assert start.await_count == 1
    sleep.assert_not_awaited()


async def test_does_not_retry_unrelated_exceptions() -> None:
    start = AsyncMock(side_effect=RuntimeError("boom"))
    sleep = AsyncMock()
    with pytest.raises(RuntimeError):
        await start_with_retry(start, POLICY, sleep=sleep)
    assert start.await_count == 1


def test_policy_rejects_nonsense() -> None:
    with pytest.raises(ValueError):
        RetryPolicy(max_attempts=0, base_delay_seconds=1.0, max_delay_seconds=5.0)
    with pytest.raises(ValueError):
        RetryPolicy(max_attempts=3, base_delay_seconds=0.0, max_delay_seconds=5.0)
    with pytest.raises(ValueError):
        RetryPolicy(max_attempts=3, base_delay_seconds=6.0, max_delay_seconds=5.0)
