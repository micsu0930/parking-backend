from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
import models


def get_parking_spots(db: Session, active_only: bool = True) -> List[models.ParkingSpot]:
    """Fetch parking spots from the database. Default filters for active spots."""
    query = db.query(models.ParkingSpot)
    if active_only:
        query = query.filter(models.ParkingSpot.is_active.is_(True))
    return query.all()


def get_spot_by_id(db: Session, spot_id: int) -> Optional[models.ParkingSpot]:
    """Fetch a single parking spot by its ID."""
    return db.query(models.ParkingSpot).filter(models.ParkingSpot.id == spot_id).first()


def check_time_overlap(
    db: Session, 
    spot_id: int, 
    start_time: datetime, 
    end_time: datetime, 
    exclude_reservation_id: Optional[int] = None
) -> bool:

    query = db.query(models.Reservation).filter(
        models.Reservation.spot_id == spot_id,
        models.Reservation.status == models.ReservationStatus.ACTIVE.value,
        models.Reservation.start_time < end_time,
        models.Reservation.end_time > start_time
    )
    
    if exclude_reservation_id:
        query = query.filter(models.Reservation.id != exclude_reservation_id)
    return query.first() is not None


def create_reservation(
    db: Session,
    spot_id: int,
    requester_name: str,
    requester_email: str,
    start_time: datetime,
    end_time: datetime,
) -> models.Reservation:
    """Create and save a new reservation after validating time availability."""
    if check_time_overlap(db, spot_id=spot_id, start_time=start_time, end_time=end_time):
        raise ValueError("Parking spot is already reserved for the requested time slot.")

    db_reservation = models.Reservation(
        spot_id=spot_id,
        requester_name=requester_name,
        requester_email=requester_email,
        start_time=start_time,
        end_time=end_time,
        status=models.ReservationStatus.ACTIVE,
    )
    db.add(db_reservation)
    db.commit()
    db.refresh(db_reservation)
    return db_reservation


def cancel_reservation(db: Session, reservation_id: int) -> Optional[models.Reservation]:
    """Cancel an existing reservation by setting its status to CANCELLED."""
    reservation = db.query(models.Reservation).filter(models.Reservation.id == reservation_id).first()
    if not reservation:
        return None

    reservation.status = models.ReservationStatus.CANCELLED
    db.commit()
    db.refresh(reservation)
    return reservation