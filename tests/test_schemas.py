from medialab_bot.schemas.system import HealthResponse
from medialab_bot.schemas.tmdb import TmdbSearchResult, TmdbSearchResponse


def test_health_response_parses():
    data = {"status": "online", "uptime_seconds": 123.45, "vpn_interface_bound": True}
    model = HealthResponse(**data)
    assert model.status == "online"
    assert model.uptime_seconds == 123.45
    assert model.vpn_interface_bound is True


def test_health_response_vpn_false():
    data = {"status": "online", "uptime_seconds": 0.0, "vpn_interface_bound": False}
    model = HealthResponse(**data)
    assert model.vpn_interface_bound is False


def test_tmdb_search_result_parses():
    data = {
        "tmdb_id": 123,
        "title": "Dune",
        "year": "2021",
        "media_type": "movie",
        "overview": "A desert planet.",
        "vote_average": 7.9,
        "poster_path": "/abc.jpg",
    }
    result = TmdbSearchResult(**data)
    assert result.tmdb_id == 123
    assert result.title == "Dune"
    assert result.poster_path == "/abc.jpg"


def test_tmdb_search_result_null_poster():
    data = {
        "tmdb_id": 1,
        "title": "No Poster",
        "year": "2020",
        "media_type": "tv",
        "overview": "",
        "vote_average": 0.0,
        "poster_path": None,
    }
    result = TmdbSearchResult(**data)
    assert result.poster_path is None


def test_tmdb_search_response_parses():
    data = {
        "status": "success",
        "message": "",
        "data": [
            {
                "tmdb_id": 1,
                "title": "Movie A",
                "year": "2022",
                "media_type": "movie",
                "overview": "Overview.",
                "vote_average": 6.5,
                "poster_path": None,
            }
        ],
    }
    response = TmdbSearchResponse(**data)
    assert len(response.data) == 1
    assert response.data[0].title == "Movie A"
