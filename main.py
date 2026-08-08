from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import engine, Base, get_db
import models
import crud
import schemas
from seed import seed_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables automatically on startup
    Base.metadata.create_all(bind=engine)
    try:
        seed_data()
    except Exception as e:
        print(f"Startup seed notice: {e}")
    yield


app = FastAPI(
    title="Parking Spot Reservation API",
    description="Backend API for managing parking spots and reservations",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/", response_model=schemas.MessageResponse, tags=["Health"])
def root():
    return {"message": "Parking Spot Reservation API is running"}


@app.get("/spots", response_model=List[schemas.ParkingSpotResponse], tags=["Parking Spots"])
def read_parking_spots(active_only: bool = True, db: Session = Depends(get_db)):
    """Fetch all parking spots (filtered for active spots by default)."""
    return crud.get_parking_spots(db, active_only=active_only)


@app.get("/spots/{spot_id}", response_model=schemas.ParkingSpotResponse, tags=["Parking Spots"])
def read_parking_spot(spot_id: int, db: Session = Depends(get_db)):
    """Fetch a specific parking spot by ID."""
    spot = crud.get_spot_by_id(db, spot_id=spot_id)
    if not spot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parking spot not found")
    return spot


@app.post("/reservations", response_model=schemas.ReservationResponse, status_code=status.HTTP_201_CREATED, tags=["Reservations"])
def create_reservation(payload: schemas.ReservationCreate, db: Session = Depends(get_db)):
    """Create a new reservation for a parking spot."""
    # 1. Verify parking spot exists
    spot = crud.get_spot_by_id(db, spot_id=payload.spot_id)
    if not spot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parking spot not found")

    # 2. Verify parking spot is active
    if not spot.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Parking spot is currently inactive")

    # 3. Create reservation and catch validation errors
    try:
        reservation = crud.create_reservation(
            db=db,
            spot_id=payload.spot_id,
            requester_name=payload.requester_name,
            requester_email=payload.requester_email,
            start_time=payload.start_time,
            end_time=payload.end_time,
        )
        return reservation
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(err))


@app.get("/spots/{spot_id}/reservations", response_model=List[schemas.ReservationResponse], tags=["Reservations"])
def read_reservations_for_spot(spot_id: int, active_only: bool = False, db: Session = Depends(get_db)):
    """Fetch all reservations for a specific parking spot."""
    spot = crud.get_spot_by_id(db, spot_id=spot_id)
    if not spot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parking spot not found")

    return crud.get_reservations_for_spot(db, spot_id=spot_id, active_only=active_only)


@app.patch("/reservations/{reservation_id}/cancel", response_model=schemas.ReservationResponse, tags=["Reservations"])
def cancel_reservation(reservation_id: int, db: Session = Depends(get_db)):
    """Cancel an existing reservation by ID."""
    reservation = crud.cancel_reservation(db, reservation_id=reservation_id)
    if not reservation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found")
    return reservation
