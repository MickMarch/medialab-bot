from pydantic import BaseModel


class TorrentResult(BaseModel):
    fileName: str
    fileUrl: str
    nbSeeders: int
    nbLeechers: int
    fileSize: int


class TorrentSearchResponse(BaseModel):
    status: str
    message: str
    data: dict[str, list[TorrentResult]]
