import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
from models import ParkingSpot, Reservation, SpotType, ReservationStatus
from seed import seed_data


TEST_DATABASE_URL = "sqlite:///:memory:"
@pytest.fixture
def db_session():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_create_parking_spot(db_session):
    """Test creating a ParkingSpot model and verifying default values."""
    spot = ParkingSpot(
        spot_number="A-101",
        spot_type=SpotType.STANDARD,
        is_active=True,
    )
    db_session.add(spot)
    db_session.commit()

    retrieved = db_session.query(ParkingSpot).filter_by(spot_number="A-101").first()
    assert retrieved is not None
    assert retrieved.id is not None
    assert retrieved.spot_type == SpotType.STANDARD
    assert retrieved.is_active is True


def test_unique_spot_number_constraint(db_session):
    """Test that creating duplicate spot numbers raises an IntegrityError."""
    from sqlalchemy.exc import IntegrityError

    spot1 = ParkingSpot(spot_number="B-201", spot_type=SpotType.EV_CHARGING)
    spot2 = ParkingSpot(spot_number="B-201", spot_type=SpotType.STANDARD)

    db_session.add(spot1)
    db_session.commit()

    db_session.add(spot2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_create_reservation_and_relationship(db_session):
    """Test creating a Reservation linked to a ParkingSpot and checking ORM relationships."""
    from datetime import datetime, timedelta, timezone

    spot = ParkingSpot(spot_number="C-301", spot_type=SpotType.HANDICAPPED)
    db_session.add(spot)
    db_session.commit()

    now = datetime.now(timezone.utc)
    reservation = Reservation(
        spot_id=spot.id,
        requester_name="John Doe",
        requester_email="john@example.com",
        start_time=now,
        end_time=now + timedelta(hours=2),
        status=ReservationStatus.ACTIVE,
    )
    db_session.add(reservation)
    db_session.commit()

    res = db_session.query(Reservation).first()
    assert res is not None
    assert res.spot_id == spot.id
    assert res.spot.spot_number == "C-301"

    assert len(spot.reservations) == 1
    assert spot.reservations[0].requester_name == "John Doe"


def test_seed_data_execution():
    """Test executing seed_data and verifying created spots and reservations."""
    from database import SessionLocal

    seed_data()

    db = SessionLocal()
    try:
        # Verify total counts
        spots = db.query(ParkingSpot).all()
        reservations = db.query(Reservation).all()

        assert len(spots) == 7
        assert len(reservations) == 2

        # Verify specific spot numbers and types
        spot_dict = {s.spot_number: s.spot_type for s in spots}
        assert spot_dict.get("A-101") == SpotType.STANDARD
        assert spot_dict.get("B-201") == SpotType.EV_CHARGING
        assert spot_dict.get("C-301") == SpotType.HANDICAPPED
        assert spot_dict.get("V-001") == SpotType.VIP

        # Verify reservation details and relationships
        requester_names = [r.requester_name for r in reservations]
        assert "John Doe" in requester_names
        assert "Jane Smith" in requester_names

        for res in reservations:
            assert res.status == ReservationStatus.ACTIVE
            assert res.spot is not None
            assert res.spot.is_active is True
    finally:
        db.close()
