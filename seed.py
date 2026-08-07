from datetime import datetime, timedelta, timezone
from database import SessionLocal, engine, Base
from models import ParkingSpot, Reservation, SpotType, ReservationStatus


def seed_data():
    # Ensure all tables exist in the database
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if database is already seeded
        existing_spots_count = db.query(ParkingSpot).count()
        if existing_spots_count > 0:
            print("Database already seeded. Skipping seed process.")
            return

        print("Seeding database with initial data...")

        # 1. Create Parking Spots
        initial_spots = [
            ParkingSpot(spot_number="A-101", spot_type=SpotType.STANDARD, is_active=True),
            ParkingSpot(spot_number="A-102", spot_type=SpotType.STANDARD, is_active=True),
            ParkingSpot(spot_number="A-103", spot_type=SpotType.STANDARD, is_active=True),
            ParkingSpot(spot_number="B-201", spot_type=SpotType.EV_CHARGING, is_active=True),
            ParkingSpot(spot_number="B-202", spot_type=SpotType.EV_CHARGING, is_active=True),
            ParkingSpot(spot_number="C-301", spot_type=SpotType.HANDICAPPED, is_active=True),
            ParkingSpot(spot_number="V-001", spot_type=SpotType.VIP, is_active=True),
        ]

        db.add_all(initial_spots)
        db.flush()  # Assigns IDs to initial_spots so we can reference them in reservations

        # 2. Create Sample Reservations
        now = datetime.now(timezone.utc)
        sample_reservations = [
            Reservation(
                spot_id=initial_spots[0].id,
                requester_name="John Doe",
                requester_email="john.doe@example.com",
                start_time=now + timedelta(hours=1),
                end_time=now + timedelta(hours=3),
                status=ReservationStatus.ACTIVE,
            ),
            Reservation(
                spot_id=initial_spots[3].id,
                requester_name="Jane Smith",
                requester_email="jane.smith@example.com",
                start_time=now + timedelta(days=1),
                end_time=now + timedelta(days=1, hours=4),
                status=ReservationStatus.ACTIVE,
            ),
        ]

        db.add_all(sample_reservations)
        db.commit()
        print("Successfully seeded initial parking spots and reservations!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
