from medialab_bot.embeds import storage_embed, transfers_embed
from medialab_bot.schemas.system import DiskUsageResponse
from medialab_bot.schemas.transfers import TransferInfo, TransferInfoResponse


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
    response = DiskUsageResponse(
        status="success",
        path="/media",
        total_gb=2000.0,
        used_gb=800.0,
        free_gb=1200.0,
        used_percent=40.0,
    )
    embed = storage_embed(response)
    combined = " ".join(f.value or "" for f in embed.fields) + (embed.description or "")
    assert "1200" in combined or "1200.0" in combined


def test_storage_embed_contains_used_percent():
    response = DiskUsageResponse(
        status="success",
        path="/media",
        total_gb=2000.0,
        used_gb=800.0,
        free_gb=1200.0,
        used_percent=40.0,
    )
    embed = storage_embed(response)
    combined = " ".join(f.value or "" for f in embed.fields) + (embed.description or "")
    assert "40" in combined
