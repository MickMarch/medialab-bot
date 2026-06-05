from medialab_bot.embeds import search_results_embed, transfers_embed, storage_embed
from medialab_bot.schemas.tmdb import TmdbSearchResult
from medialab_bot.schemas.transfers import TransferInfo, TransferInfoResponse
from medialab_bot.schemas.system import DiskUsage, StorageResponse


def _make_transfer(**kwargs) -> TransferInfo:
    defaults = {
        "name": "Dune.2021.mkv",
        "size": 8_000_000_000,
        "progress": 0.45,
        "hash": "abc123",
        "state": "downloading",
        "download_speed": 5_000_000,
        "upload_speed": 0,
        "eta_seconds": 900,
        "save_path": "/media/downloads",
    }
    return TransferInfo(**{**defaults, **kwargs})


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


# --- transfers_embed ---

def test_transfers_embed_one_field_per_transfer():
    transfers = [_make_transfer(name=f"Movie{i}.mkv") for i in range(3)]
    response = TransferInfoResponse(status="success", message="", data=transfers)
    embed = transfers_embed(response)
    assert len(embed.fields) == 3


def test_transfers_embed_field_contains_name_and_progress():
    t = _make_transfer(name="Dune.mkv", progress=0.75, state="downloading")
    response = TransferInfoResponse(status="success", message="", data=[t])
    embed = transfers_embed(response)
    field = embed.fields[0]
    assert "Dune.mkv" in field.name
    assert "75" in (field.value or "") or "75" in field.name


def test_transfers_embed_field_contains_state():
    t = _make_transfer(state="seeding")
    response = TransferInfoResponse(status="success", message="", data=[t])
    embed = transfers_embed(response)
    field = embed.fields[0]
    assert "seeding" in (field.value or "").lower() or "seeding" in field.name.lower()


# --- storage_embed ---

def test_storage_embed_contains_free_gb():
    response = StorageResponse(
        status="success",
        message="",
        data=DiskUsage(path="/media", total_gb=2000.0, used_gb=800.0, free_gb=1200.0, used_percent=40.0),
    )
    embed = storage_embed(response)
    combined = " ".join(f.value or "" for f in embed.fields) + (embed.description or "")
    assert "1200" in combined or "1200.0" in combined


def test_storage_embed_contains_used_percent():
    response = StorageResponse(
        status="success",
        message="",
        data=DiskUsage(path="/media", total_gb=2000.0, used_gb=800.0, free_gb=1200.0, used_percent=40.0),
    )
    embed = storage_embed(response)
    combined = " ".join(f.value or "" for f in embed.fields) + (embed.description or "")
    assert "40" in combined
