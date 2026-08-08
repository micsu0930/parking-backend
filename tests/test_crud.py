import os
import sys
from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database import Base
import models
import crud


TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def db_session():
    """Provides a clean in-memory SQLite database session for each test."""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_get_parking_spots(db_session):
    """Test fetching active parking spots and all parking spots."""
    spot1 = models.ParkingSpot(spot_number="A-01", spot_type=models.SpotType.STANDARD, is_active=True)
    spot2 = models.ParkingSpot(spot_number="A-02", spot_type=models.SpotType.EV_CHARGING, is_active=False)
    db_session.add_all([spot1, spot2])
    db_session.commit()

    active_spots = crud.get_parking_spots(db_session, active_only=True)
    assert len(active_spots) == 1
    assert active_spots[0].spot_number == "A-01"

    all_spots = crud.get_parking_spots(db_session, active_only=False)
    assert len(all_spots) == 2


def test_get_spot_by_id(db_session):
    """Test retrieving a spot by ID."""
    spot = models.ParkingSpot(spot_number="B-01", spot_type=models.SpotType.HANDICAPPED)
    db_session.add(spot)
    db_session.commit()

    found_spot = crud.get_spot_by_id(db_session, spot.id)
    assert found_spot is not None
    assert found_spot.spot_number == "B-01"

    non_existent = crud.get_spot_by_id(db_session, 999)
    assert non_existent is None


def test_check_time_overlap(db_session):
    """Test detecting overlapping reservation intervals."""
    spot = models.ParkingSpot(spot_number="C-01", spot_type=models.SpotType.VIP)
    db_session.add(spot)
    db_session.commit()

    base_time = datetime.now(timezone.utc)
    res = models.Reservation(
        spot_id=spot.id,
        requester_name="Test User",
        requester_email="test@example.com",
        start_time=base_time + timedelta(hours=2),
        end_time=base_time + timedelta(hours=4),
        status=models.ReservationStatus.ACTIVE,
    )
    db_session.add(res)
    db_session.commit()

    # Overlapping interval (overlaps 3:00 to 5:00)
    has_overlap = crud.check_time_overlap(
        db_session,
        spot_id=spot.id,
        start_time=base_time + timedelta(hours=3),
        end_time=base_time + timedelta(hours=5),
    )
    assert has_overlap is True

    # Non-overlapping interval (5:00 to 6:00)
    no_overlap = crud.check_time_overlap(
        db_session,
        spot_id=spot.id,
        start_time=base_time + timedelta(hours=5),
        end_time=base_time + timedelta(hours=6),
    )
    assert no_overlap is False

    # Exclude existing reservation ID
    excluded_overlap = crud.check_time_overlap(
        db_session,
        spot_id=spot.id,
        start_time=base_time + timedelta(hours=2),
        end_time=base_time + timedelta(hours=4),
        exclude_reservation_id=res.id,
    )
    assert excluded_overlap is False


def test_create_reservation_success(db_session):
    """Test successfully creating a reservation."""
    spot = models.ParkingSpot(spot_number="D-01", spot_type=models.SpotType.STANDARD)
    db_session.add(spot)
    db_session.commit()

    now = datetime.now(timezone.utc)
    res = crud.create_reservation(
        db=db_session,
        spot_id=spot.id,
        requester_name="Alice Smith",
        requester_email="alice@example.com",
        start_time=now + timedelta(hours=1),
        end_time=now + timedelta(hours=3),
    )
    assert res.id is not None
    assert res.requester_name == "Alice Smith"
    assert res.status == models.ReservationStatus.ACTIVE


def test_create_reservation_invalid_times(db_session):
    """Test creating a reservation where end_time <= start_time raises ValueError."""
    spot = models.ParkingSpot(spot_number="D-02", spot_type=models.SpotType.STANDARD)
    db_session.add(spot)
    db_session.commit()

    now = datetime.now(timezone.utc)
    with pytest.raises(ValueError, match="Reservation end time must be after start time"):
        crud.create_reservation(
            db=db_session,
            spot_id=spot.id,
            requester_name="Invalid Time User",
            requester_email="user@example.com",
            start_time=now + timedelta(hours=3),
            end_time=now + timedelta(hours=1),
        )


def test_create_reservation_overlap_conflict(db_session):
    """Test creating a reservation that conflicts with an existing reservation raises ValueError."""
    spot = models.ParkingSpot(spot_number="D-03", spot_type=models.SpotType.STANDARD)
    db_session.add(spot)
    db_session.commit()

    now = datetime.now(timezone.utc)
    crud.create_reservation(
        db=db_session,
        spot_id=spot.id,
        requester_name="First User",
        requester_email="first@example.com",
        start_time=now + timedelta(hours=1),
        end_time=now + timedelta(hours=4),
    )

    with pytest.raises(ValueError, match="already reserved"):
        crud.create_reservation(
            db=db_session,
            spot_id=spot.id,
            requester_name="Second User",
            requester_email="second@example.com",
            start_time=now + timedelta(hours=2),
            end_time=now + timedelta(hours=3),
        )


def test_cancel_reservation(db_session):
    """Test cancelling an existing reservation."""
    spot = models.ParkingSpot(spot_number="E-01", spot_type=models.SpotType.STANDARD)
    db_session.add(spot)
    db_session.commit()

    now = datetime.now(timezone.utc)
    res = crud.create_reservation(
        db=db_session,
        spot_id=spot.id,
        requester_name="Bob Brown",
        requester_email="bob@example.com",
        start_time=now + timedelta(hours=1),
        end_time=now + timedelta(hours=2),
    )

    cancelled_res = crud.cancel_reservation(db_session, res.id)
    assert cancelled_res is not None
    assert cancelled_res.status == models.ReservationStatus.CANCELLED

    non_existent = crud.cancel_reservation(db_session, 999)
    assert non_existent is None


def test_get_reservations_for_spot(db_session):
    """Test fetching active vs all reservations for a spot."""
    spot = models.ParkingSpot(spot_number="F-01", spot_type=models.SpotType.VIP)
    db_session.add(spot)
    db_session.commit()

    now = datetime.now(timezone.utc)
    res1 = crud.create_reservation(
        db=db_session,
        spot_id=spot.id,
        requester_name="User 1",
        requester_email="user1@example.com",
        start_time=now + timedelta(hours=1),
        end_time=now + timedelta(hours=2),
    )
    res2 = crud.create_reservation(
        db=db_session,
        spot_id=spot.id,
        requester_name="User 2",
        requester_email="user2@example.com",
        start_time=now + timedelta(hours=3),
        end_time=now + timedelta(hours=4),
    )

    # Cancel res1
    crud.cancel_reservation(db_session, res1.id)

    all_reservations = crud.get_reservations_for_spot(db_session, spot.id, active_only=False)
    assert len(all_reservations) == 2

    active_reservations = crud.get_reservations_for_spot(db_session, spot.id, active_only=True)
    assert len(active_reservations) == 1
    assert active_reservations[0].id == res2.id