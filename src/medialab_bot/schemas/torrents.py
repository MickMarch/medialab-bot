from pydantic import BaseModel, ConfigDict, Field


class TorrentResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    file_name: str = Field(alias="fileName")
    file_url: str = Field(alias="fileUrl")
    seeders: int = Field(alias="nbSeeders", ge=0)
    leechers: int = Field(alias="nbLeechers", ge=0)
    file_size: int = Field(alias="fileSize")


class TorrentSearchResponse(BaseModel):
    status: str
    message: str
    data: dict[str, list[TorrentResult]]
