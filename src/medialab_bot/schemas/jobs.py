"""Pipeline job views mirrored from the orchestrator gateway."""

from medialab_contracts import MediaType
from pydantic import BaseModel


class JobView(BaseModel):
    """A single pipeline job as the gateway exposes it."""

    id: int
    torrent_hash: str
    release_name: str
    media_type: MediaType
    tmdb_id: int
    resolved_title: str | None = None
    resolved_year: int | None = None
    source_path: str | None = None
    dest_path: str | None = None
    status: str
    last_error: str | None = None
    attempts: int = 0
    created_at: str
    updated_at: str


class JobsResponse(BaseModel):
    """Body of ``GET /jobs``."""

    status: str
    jobs: list[JobView]
