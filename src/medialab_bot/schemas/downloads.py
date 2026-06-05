from pydantic import BaseModel


class DownloadRequest(BaseModel):
    magnet_uri: str
    save_path: str
    dry_run: bool = False


class DownloadResponse(BaseModel):
    status: str
    message: str
