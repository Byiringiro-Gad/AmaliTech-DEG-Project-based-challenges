from pydantic import BaseModel, Field
from typing import Optional


# What the client sends when registering a new monitor
class RegisterRequest(BaseModel):
    id: str = Field(..., min_length=1)
    timeout: int = Field(..., gt=0)          # countdown in seconds, must be > 0
    alert_email: str = Field(..., min_length=3)


# What the server sends back for any monitor-related response
class MonitorResponse(BaseModel):
    id: str
    status: str                              # "active", "down", or "paused"
    timeout: int
    alert_email: str
    message: Optional[str] = None
