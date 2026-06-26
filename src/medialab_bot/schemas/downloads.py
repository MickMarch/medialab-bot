from pydantic import BaseModel

from medialab_bot.schemas.jobs import JobView


class DownloadResponse(BaseModel):
    """Body of ``POST /download``. The gateway creates a pipeline job and
    returns it so the bot can track the download by hash via ``/jobs``."""

    status: str
    job: JobView
