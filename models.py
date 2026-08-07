from datetime import datetime, timezone
import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from database import Base


# ENUMS
class SpotType(str, enum.Enum):
    STANDARD = "STANDARD"
    HANDICAPPED = "HANDICAPPED"
    EV_CHARGING = "EV_CHARGING"
    VIP = "VIP"

class ReservationStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    CANCELLED = "CANCELLED"


# DATABASE TABLES 
class ParkingSpot(Base):
    __tablename__ = "parking_spots"

    id = Column(Integer, primary_key=True, index=True)
    spot_number = Column(String, unique=True, nullable=False, index=True)
    spot_type = Column(Enum(SpotType), nullable=False, default=SpotType.STANDARD)
    is_active = Column(Boolean, default=True, nullable=False)

    reservations = relationship("Reservation", back_populates="spot")


class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    spot_id = Column(Integer, ForeignKey("parking_spots.id"), nullable=False, index=True)
    requester_name = Column(String, nullable=False)
    requester_email = Column(String, nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    status = Column(Enum(ReservationStatus), nullable=False, default=ReservationStatus.ACTIVE)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    spot = relationship("ParkingSpot", back_populates="reservations")
