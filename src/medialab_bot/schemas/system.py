from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    uptime_seconds: float
    vpn_interface_bound: bool


class DiskUsage(BaseModel):
    path: str
    total_gb: float
    used_gb: float
    free_gb: float
    used_percent: float


class StorageResponse(BaseModel):
    status: str
    message: str
    data: DiskUsage
