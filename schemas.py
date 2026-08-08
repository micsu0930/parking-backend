from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict

# PARKING SPOT
class ParkingSpotResponse(BaseModel):
    id: int
    spot_number: str
    spot_type: str
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)


# RESERVATION
class ReservationCreate(BaseModel):
    spot_id: int
    requester_name: str = Field(..., min_length=2, max_length=100)
    requester_email: EmailStr
    start_time: datetime
    end_time: datetime
    
    @field_validator("end_time")
    @classmethod
    def validate_end_time(cls, end_time: datetime, info):
        start_time = info.data.get("start_time")
        if start_time and end_time <= start_time:
            raise ValueError("Reservation end_time must be strictly after start_time.")
        return end_time


class ReservationResponse(BaseModel):
    id: int
    spot_id: int
    requester_name: str
    requester_email: str
    start_time: datetime
    end_time: datetime
    status: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    message: str