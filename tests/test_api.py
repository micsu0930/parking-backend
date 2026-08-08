from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from main import app
import models


@pytest.fixture
def client():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
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