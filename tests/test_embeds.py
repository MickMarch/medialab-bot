from medialab_bot.embeds import search_results_embed
from medialab_bot.schemas.tmdb import TmdbSearchResult


def _make_result(**kwargs) -> TmdbSearchResult:
    defaults = {
        "tmdb_id": 1,
        "title": "Test Movie",
        "year": "2024",
        "media_type": "movie",
        "overview": "A test overview.",
        "vote_average": 7.5,
        "poster_path": None,
    }
    return TmdbSearchResult(**{**defaults, **kwargs})


def test_embed_title():
    embed = search_results_embed([_make_result()])
    assert embed.title == "Search Results"


def test_embed_one_field_per_result():
    results = [_make_result(tmdb_id=i, title=f"Movie {i}") for i in range(3)]
    embed = search_results_embed(results)
    assert len(embed.fields) == 3


def test_embed_field_contains_metadata():
    result = _make_result(title="Dune", year="2021", media_type="movie", vote_average=7.9)
    embed = search_results_embed([result])
    field = embed.fields[0]
    assert "Dune" in field.name
    assert "2021" in field.name
    assert "movie" in field.name.lower() or "movie" in (field.value or "").lower()
    assert "7.9" in (field.value or "") or "7.9" in field.name


def test_embed_empty_results():
    embed = search_results_embed([])
    assert len(embed.fields) == 0
