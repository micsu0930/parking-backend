import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from database import Base, get_db
from main import app
import models


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    db = TestingSessionLocal()
    spot1 = models.ParkingSpot(spot_number="SPOT-101", spot_type=models.SpotType.STANDARD, is_active=True)
    spot2 = models.ParkingSpot(spot_number="SPOT-102", spot_type=models.SpotType.EV_CHARGING, is_active=False)
    db.add_all([spot1, spot2])
    db.commit()
    db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)



def test_root_health_check(client):
    """Test health check root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Parking Spot Reservation API is running"}


def test_get_spots_default_active_only(client):
    """Test fetching active parking spots (default active_only=true)."""
    response = client.get("/spots")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["spot_number"] == "SPOT-101"
    assert data[0]["is_active"] is True


def test_get_spots_all(client):
    """Test fetching all parking spots including inactive (active_only=false)."""
    response = client.get("/spots?active_only=false")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_spot_by_id_success(client):
    """Test retrieving a valid parking spot by ID."""
    response = client.get("/spots/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["spot_number"] == "SPOT-101"


def test_get_spot_by_id_not_found(client):
    """Test retrieving a non-existent parking spot returns 404."""
    response = client.get("/spots/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Parking spot not found"


def test_create_reservation_success(client):
    """Test creating a valid reservation."""
    now = datetime.now(timezone.utc)
    payload = {
        "spot_id": 1,
        "requester_name": "John Doe",
        "requester_email": "john.doe@example.com",
        "start_time": (now + timedelta(hours=1)).isoformat(),
        "end_time": (now + timedelta(hours=3)).isoformat(),
    }
    response = client.post("/reservations", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["spot_id"] == 1
    assert data["requester_name"] == "John Doe"
    assert data["status"] == "ACTIVE"


def test_create_reservation_spot_not_found(client):
    """Test creating a reservation for a non-existent spot returns 404."""
    now = datetime.now(timezone.utc)
    payload = {
        "spot_id": 999,
        "requester_name": "Ghost User",
        "requester_email": "ghost@example.com",
        "start_time": (now + timedelta(hours=1)).isoformat(),
        "end_time": (now + timedelta(hours=2)).isoformat(),
    }
    response = client.post("/reservations", json=payload)
    assert response.status_code == 404
    assert response.json()["detail"] == "Parking spot not found"


def test_create_reservation_inactive_spot(client):
    """Test creating a reservation for an inactive spot returns 400."""
    now = datetime.now(timezone.utc)
    payload = {
        "spot_id": 2,  # SPOT-102 is inactive
        "requester_name": "Inactive Spot User",
        "requester_email": "inactive@example.com",
        "start_time": (now + timedelta(hours=1)).isoformat(),
        "end_time": (now + timedelta(hours=2)).isoformat(),
    }
    response = client.post("/reservations", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Parking spot is currently inactive"


def test_create_reservation_time_overlap_conflict(client):
    """Test creating an overlapping reservation returns 409 Conflict."""
    now = datetime.now(timezone.utc)
    payload1 = {
        "spot_id": 1,
        "requester_name": "First User",
        "requester_email": "first@example.com",
        "start_time": (now + timedelta(hours=2)).isoformat(),
        "end_time": (now + timedelta(hours=5)).isoformat(),
    }
    res1 = client.post("/reservations", json=payload1)
    assert res1.status_code == 201

    payload2 = {
        "spot_id": 1,
        "requester_name": "Overlapping User",
        "requester_email": "overlap@example.com",
        "start_time": (now + timedelta(hours=3)).isoformat(),
        "end_time": (now + timedelta(hours=6)).isoformat(),
    }
    res2 = client.post("/reservations", json=payload2)
    assert res2.status_code == 409


def test_get_reservations_for_spot(client):
    """Test retrieving all reservations for a spot."""
    now = datetime.now(timezone.utc)
    payload = {
        "spot_id": 1,
        "requester_name": "Spot User",
        "requester_email": "spotuser@example.com",
        "start_time": (now + timedelta(hours=10)).isoformat(),
        "end_time": (now + timedelta(hours=12)).isoformat(),
    }
    client.post("/reservations", json=payload)

    response = client.get("/spots/1/reservations")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1

    notFoundRes = client.get("/spots/999/reservations")
    assert notFoundRes.status_code == 404


def test_cancel_reservation_success(client):
    """Test cancelling a reservation returns updated status."""
    now = datetime.now(timezone.utc)
    payload = {
        "spot_id": 1,
        "requester_name": "Cancel User",
        "requester_email": "cancel@example.com",
        "start_time": (now + timedelta(hours=20)).isoformat(),
        "end_time": (now + timedelta(hours=22)).isoformat(),
    }
    res = client.post("/reservations", json=payload)
    assert res.status_code == 201
    res_id = res.json()["id"]

    cancel_res = client.patch(f"/reservations/{res_id}/cancel")
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"


def test_cancel_reservation_not_found(client):
    """Test cancelling a non-existent reservation returns 404."""
    response = client.patch("/reservations/999/cancel")
    assert response.status_code == 404
    assert response.json()["detail"] == "Reservation not found"
