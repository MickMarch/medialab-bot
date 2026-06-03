from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    uptime_seconds: float
    vpn_interface_bound: bool
