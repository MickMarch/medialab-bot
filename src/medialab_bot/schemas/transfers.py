from pydantic import BaseModel


class TransferInfo(BaseModel):
    name: str
    size: int
    progress: float
    hash: str
    state: str
    download_speed: int
    upload_speed: int
    eta_seconds: int
    save_path: str


class TransferInfoResponse(BaseModel):
    status: str
    message: str
    data: list[TransferInfo]
