from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import os

# Use the connection string provided by the user
import certifi
MONGO_URL = os.getenv("MONGO_URL")
client = AsyncIOMotorClient(MONGO_URL, tlsCAFile=certifi.where())
db = client.room_booking_db

rooms_collection = db.rooms
bookings_collection = db.bookings
users_collection = db.users

async def init_db():
    # Check if rooms are already seeded
    count = await rooms_collection.count_documents({})
    if count == 0:
        print("Seeding database with rooms...")
        rooms = [
            {"_id": "room_6A", "name": "Room-6A", "capacity": 6},
            {"_id": "room_6B", "name": "Room-6B", "capacity": 6},
            {"_id": "room_6C", "name": "Room-6C", "capacity": 6},
            {"_id": "room_6D", "name": "Room-6D", "capacity": 6},
            {"_id": "room_6E", "name": "Room-6E", "capacity": 6},
            {"_id": "room_9A", "name": "Room-9A", "capacity": 9},
            {"_id": "room_9B", "name": "Room-9B", "capacity": 9},
            {"_id": "room_9C", "name": "Room-9C", "capacity": 9},
            {"_id": "room_9D", "name": "Room-9D", "capacity": 9},
            {"_id": "room_9E", "name": "Room-9E", "capacity": 9},
            {"_id": "room_11A", "name": "Room-11A", "capacity": 11},
            {"_id": "room_11B", "name": "Room-11B", "capacity": 11},
            {"_id": "room_11C", "name": "Room-11C", "capacity": 11},
            {"_id": "room_11D", "name": "Room-11D", "capacity": 11},
            {"_id": "room_11E", "name": "Room-11E", "capacity": 11},
            {"_id": "room_15A", "name": "Room-15A", "capacity": 15},
            {"_id": "room_15B", "name": "Room-15B", "capacity": 15},
        ]
        await rooms_collection.insert_many(rooms)
        print("Database seeded with 17 rooms.")

        # Create unique index to prevent double booking
        # We want to ensure that for a given room, date, and time slot, there is only one booking
        # For simplicity in this implementation, we'll just index on room_id, date, start_time
        await bookings_collection.create_index(
            [("room_id", 1), ("date", 1), ("start_time", 1)],
            unique=True,
            name="unique_booking_slot"
        )
    else:
        print(f"Database already contains {count} rooms.")
