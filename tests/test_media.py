from medialab_contracts import MediaType

from medialab_bot.media import from_tmdb_media_type


def test_movie_maps_to_movie():
    assert from_tmdb_media_type("movie") is MediaType.MOVIE


def test_tv_maps_to_show():
    assert from_tmdb_media_type("tv") is MediaType.SHOW


def test_show_maps_to_show():
    assert from_tmdb_media_type("show") is MediaType.SHOW


def test_case_insensitive():
    assert from_tmdb_media_type("TV") is MediaType.SHOW


def test_unknown_returns_none():
    assert from_tmdb_media_type("person") is None
