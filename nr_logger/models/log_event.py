from datetime import datetime
from pydantic import BaseModel, Field


class LogEvent(BaseModel):

    application: str
    service: str
    environment: str
    severity: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    additional_details: dict = {}
