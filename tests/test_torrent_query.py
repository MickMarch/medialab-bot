"""The torrent search pattern: ``Title YYYY`` for a movie, the bare title for
a show, never a parenthesised year (it poisons release-name matching)."""

from medialab_contracts import MediaType

from medialab_bot.views.torrent import torrent_query


def test_movie_query_is_title_then_bare_year():
    assert torrent_query("Dune", "2021", MediaType.MOVIE) == "Dune 2021"


def test_show_query_is_the_bare_title():
    assert torrent_query("Lost", "2004", MediaType.SHOW) == "Lost"


def test_no_parentheses_in_any_query():
    for media_type in MediaType:
        assert "(" not in torrent_query("Dune", "2021", media_type)
