from pydantic import BaseModel


class DownloadResponse(BaseModel):
    status: str
    message: str
