import pytest
from unittest.mock import AsyncMock, MagicMock

from medialab_bot.schemas.tmdb import TmdbSearchResponse, TmdbSearchResult
from medialab_bot.cogs.search import SearchCog


def _make_result(tmdb_id: int = 1, title: str = "Test Movie") -> TmdbSearchResult:
    return TmdbSearchResult(
        tmdb_id=tmdb_id,
        title=title,
        year="2024",
        media_type="movie",
        overview="Overview.",
        vote_average=7.0,
        poster_path=None,
    )


def _make_response(results: list[TmdbSearchResult]) -> TmdbSearchResponse:
    return TmdbSearchResponse(status="success", message="", data=results)


def _make_interaction() -> MagicMock:
    interaction = MagicMock()
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.defer = AsyncMock()
    interaction.followup = MagicMock()
    interaction.followup.send = AsyncMock()
    return interaction


@pytest.mark.asyncio
async def test_search_defers_before_api_call(mock_client):
    mock_client.search_tmdb = AsyncMock(return_value=_make_response([_make_result()]))
    cog = SearchCog(mock_client)
    interaction = _make_interaction()

    await cog.search.callback(cog, interaction, query="dune")

    interaction.response.defer.assert_awaited_once()


@pytest.mark.asyncio
async def test_search_sends_embed_and_view_on_results(mock_client):
    mock_client.search_tmdb = AsyncMock(return_value=_make_response([_make_result()]))
    cog = SearchCog(mock_client)
    interaction = _make_interaction()

    await cog.search.callback(cog, interaction, query="dune")

    mock_client.search_tmdb.assert_awaited_once_with("dune")
    interaction.followup.send.assert_awaited_once()
    call_kwargs = interaction.followup.send.call_args.kwargs
    assert call_kwargs.get("embed") is not None
    assert call_kwargs.get("view") is not None


@pytest.mark.asyncio
async def test_search_sends_ephemeral_error_on_empty_results(mock_client):
    mock_client.search_tmdb = AsyncMock(return_value=_make_response([]))
    cog = SearchCog(mock_client)
    interaction = _make_interaction()

    await cog.search.callback(cog, interaction, query="xyzzy")

    interaction.followup.send.assert_awaited_once()
    call_kwargs = interaction.followup.send.call_args.kwargs
    assert call_kwargs.get("ephemeral") is True


@pytest.mark.asyncio
async def test_search_sends_ephemeral_error_on_client_none(mock_client):
    mock_client.search_tmdb = AsyncMock(return_value=None)
    cog = SearchCog(mock_client)
    interaction = _make_interaction()

    await cog.search.callback(cog, interaction, query="dune")

    interaction.followup.send.assert_awaited_once()
    call_kwargs = interaction.followup.send.call_args.kwargs
    assert call_kwargs.get("ephemeral") is True


@pytest.mark.asyncio
async def test_select_callback_replies_with_selected_title(mock_client):
    from medialab_bot.cogs.search import TmdbSelectMenu

    results = [_make_result(tmdb_id=42, title="Dune")]
    view = TmdbSelectMenu(results)
    interaction = _make_interaction()
    interaction.configure_mock(data={"values": ["42:movie"]})

    await view.select.callback(interaction)

    interaction.response.send_message.assert_awaited_once()
    call = interaction.response.send_message.call_args
    content = call.args[0] if call.args else call.kwargs.get("content", "")
    assert "Dune" in content
    assert "2024" in content


@pytest.mark.asyncio
async def test_select_callback_handles_malformed_data(mock_client):
    from medialab_bot.cogs.search import TmdbSelectMenu

    results = [_make_result(tmdb_id=42, title="Dune")]
    view = TmdbSelectMenu(results)
    interaction = _make_interaction()
    interaction.data = {}

    await view.select.callback(interaction)

    interaction.response.send_message.assert_awaited_once()
    call_kwargs = interaction.response.send_message.call_args.kwargs
    assert call_kwargs.get("ephemeral") is True
