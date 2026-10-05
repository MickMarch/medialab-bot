from unittest.mock import AsyncMock

import pytest
from medialab_contracts import SettingSource, SettingType, SettingView, SuiteSettingsResponse

from medialab_bot.cogs.settings import SettingsCog
from tests.helpers import make_interaction

DOWNLOADER = "torrent-downloader"
ORCHESTRATOR = "medialab-orchestrator"


def _view(
    key: str, value, *, source=SettingSource.ENV, applies="next search", **extra
) -> SettingView:
    return SettingView(
        key=key,
        value=value,
        default=value,
        source=source,
        type=SettingType.INT if isinstance(value, int) else SettingType.STR,
        description=f"{key} description",
        applies=applies,
        **extra,
    )


def _suite() -> SuiteSettingsResponse:
    return SuiteSettingsResponse(
        status="success",
        services={
            DOWNLOADER: [
                _view("minimum_seeders", 5, source=SettingSource.OVERRIDE),
                _view("target_language", "en"),
            ],
            ORCHESTRATOR: [_view("auto_retry_max", 3, applies="next poll tick")],
        },
    )


def _cog(mock_client) -> SettingsCog:
    mock_client.get_settings = AsyncMock(return_value=_suite())
    return SettingsCog(mock_client)


# --- /settings show ---


@pytest.mark.asyncio
async def test_show_lists_every_service_and_key_with_source(mock_client):
    cog = _cog(mock_client)
    interaction = make_interaction()

    await cog.show.callback(cog, interaction)

    embed = interaction.followup.send.call_args.kwargs["embed"]
    names = [f.name for f in embed.fields]
    assert DOWNLOADER in names and ORCHESTRATOR in names
    downloader = next(f for f in embed.fields if f.name == DOWNLOADER).value
    assert "minimum_seeders" in downloader and "5" in downloader and "override" in downloader
    assert "target_language" in downloader and "en" in downloader
    assert interaction.followup.send.call_args.kwargs.get("ephemeral") is True


@pytest.mark.asyncio
async def test_show_reports_a_gateway_failure(mock_client):
    mock_client.get_settings = AsyncMock(return_value=None)
    cog = SettingsCog(mock_client)
    interaction = make_interaction()

    await cog.show.callback(cog, interaction)

    assert "Failed" in interaction.followup.send.call_args.args[0]


# --- /settings set ---


@pytest.mark.asyncio
async def test_set_forwards_service_key_value_and_states_when_it_applies(mock_client):
    cog = _cog(mock_client)
    mock_client.set_setting = AsyncMock(
        return_value=_view("minimum_seeders", 10, source=SettingSource.OVERRIDE)
    )
    interaction = make_interaction()

    await cog.set.callback(cog, interaction, service=DOWNLOADER, key="minimum_seeders", value="10")

    mock_client.set_setting.assert_awaited_once_with(DOWNLOADER, "minimum_seeders", "10")
    message = interaction.followup.send.call_args.args[0]
    assert "minimum_seeders" in message and "10" in message
    assert "next search" in message


@pytest.mark.asyncio
async def test_set_refusal_names_the_key(mock_client):
    cog = _cog(mock_client)
    mock_client.set_setting = AsyncMock(return_value=None)
    interaction = make_interaction()

    await cog.set.callback(cog, interaction, service=DOWNLOADER, key="minimum_seeders", value="x")

    message = interaction.followup.send.call_args.args[0]
    assert "minimum_seeders" in message
    assert "not" in message.lower()


# --- /settings reset ---


@pytest.mark.asyncio
async def test_reset_forwards_and_reports_the_restored_value(mock_client):
    cog = _cog(mock_client)
    mock_client.reset_setting = AsyncMock(return_value=_view("minimum_seeders", 3))
    interaction = make_interaction()

    await cog.reset.callback(cog, interaction, service=DOWNLOADER, key="minimum_seeders")

    mock_client.reset_setting.assert_awaited_once_with(DOWNLOADER, "minimum_seeders")
    message = interaction.followup.send.call_args.args[0]
    assert "minimum_seeders" in message and "3" in message and "next search" in message


@pytest.mark.asyncio
async def test_reset_refusal_names_the_key(mock_client):
    cog = _cog(mock_client)
    mock_client.reset_setting = AsyncMock(return_value=None)
    interaction = make_interaction()

    await cog.reset.callback(cog, interaction, service=ORCHESTRATOR, key="nope")

    assert "nope" in interaction.followup.send.call_args.args[0]


# --- autocomplete ---


@pytest.mark.asyncio
async def test_service_autocomplete_lists_services_matching_the_typed_text(mock_client):
    cog = _cog(mock_client)

    choices = await cog.service_autocomplete(make_interaction(), "orch")

    assert [c.value for c in choices] == [ORCHESTRATOR]


@pytest.mark.asyncio
async def test_key_autocomplete_is_scoped_to_the_chosen_service(mock_client):
    cog = _cog(mock_client)
    interaction = make_interaction()
    interaction.namespace.service = ORCHESTRATOR

    choices = await cog.key_autocomplete(interaction, "")

    assert [c.value for c in choices] == ["auto_retry_max"]


@pytest.mark.asyncio
async def test_key_autocomplete_without_a_service_lists_every_key(mock_client):
    cog = _cog(mock_client)
    interaction = make_interaction()
    interaction.namespace.service = None

    choices = await cog.key_autocomplete(interaction, "m")

    assert [c.value for c in choices] == ["minimum_seeders", "auto_retry_max"]


@pytest.mark.asyncio
async def test_autocomplete_is_empty_when_the_gateway_is_down(mock_client):
    mock_client.get_settings = AsyncMock(return_value=None)
    cog = SettingsCog(mock_client)

    assert await cog.service_autocomplete(make_interaction(), "") == []
