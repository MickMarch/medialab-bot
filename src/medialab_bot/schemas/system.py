from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    uptime_seconds: float
    vpn_interface_bound: bool


class DiskUsageResponse(BaseModel):
    status: str
    path: str
    total_gb: float
    used_gb: float
    free_gb: float
    used_percent: float
