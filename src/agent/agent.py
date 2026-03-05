import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.tools import tool
from typing import Annotated, Literal
import datetime
import uuid
from src.database.db import rooms_collection, bookings_collection


# Define LLM with fallback dummy key so server can still start
api_key = os.getenv("OPENAI_API_KEY")
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=api_key)

@tool
async def check_availability(date: str, start_time: str, end_time: str, capacity: int, room_name: str = None) -> str:
    """Check room availability for a given date, time range, minimum capacity, and optional room name.
    
    Args:
        date: The date in YYYY-MM-DD format.
        start_time: The start time in HH:MM format (24-hour).
        end_time: The end time in HH:MM format (24-hour).
        capacity: The number of people attending the meeting.
        room_name: (Optional) The specific name of the room to check.
        
    Returns:
        A string describing available rooms or a message if none are available.
    """
    cursor = rooms_collection.find({"capacity": {"$gte": capacity}}).sort("capacity", 1)
    eligible_rooms = await cursor.to_list(length=100)

    if room_name:
        # Check specific room. Make regex flexible (e.g. '6a' or 'room 6a' matches 'Room-6A')
        clean_name = room_name.replace("Room ", "").replace("room ", "").replace("-", "")
        requested_room = await rooms_collection.find_one({"name": {"$regex": f"{clean_name}$", "$options": "i"}})
        if not requested_room:
            return f"Room {room_name} does not exist in our database."
        
        if requested_room["capacity"] < capacity:
            if not eligible_rooms:
                return f"Room {requested_room['name']} is a {requested_room['capacity']} seater room which is not available for {capacity} people."
            
            eligible_room_ids = [room["_id"] for room in eligible_rooms]
            conflicting_bookings_cursor = bookings_collection.find({
                "room_id": {"$in": eligible_room_ids},
                "date": date,
                "start_time": {"$lt": end_time},
                "end_time": {"$gt": start_time}
            })
            conflicting_bookings = await conflicting_bookings_cursor.to_list(length=100)
            booked_room_ids = [booking["room_id"] for booking in conflicting_bookings]
            available_rooms = [r for r in eligible_rooms if r["_id"] not in booked_room_ids]
            
            if available_rooms:
                alt_room = available_rooms[0]
                return f"Room {requested_room['name']} is a {requested_room['capacity']} seater room which is not available for {capacity} people. You can use {alt_room['name']} which can accommodate {capacity} people easily."
            else:
                return f"Room {requested_room['name']} is a {requested_room['capacity']} seater room which is not available for {capacity} people, and all other suitable rooms are booked."
        else:
            conflict = await bookings_collection.find_one({
                "room_id": requested_room["_id"],
                "date": date,
                "start_time": {"$lt": end_time},
                "end_time": {"$gt": start_time}
            })
            if conflict:
                return f"Room {requested_room['name']} is already booked at {start_time}."
            return f"Room {requested_room['name']} (capacity {requested_room['capacity']}) is available."
            
    else:
        # Standard behaviour with no specific room
        if not eligible_rooms:
            return f"Room capacity is not enough. The requested capacity ({capacity} people) exceeds our largest available room."
            
        eligible_room_ids = [room["_id"] for room in eligible_rooms]
        
        conflicting_bookings_cursor = bookings_collection.find({
            "room_id": {"$in": eligible_room_ids},
            "date": date,
            "start_time": {"$lt": end_time},
            "end_time": {"$gt": start_time}
        })
        conflicting_bookings = await conflicting_bookings_cursor.to_list(length=100)
        
        booked_room_ids = [booking["room_id"] for booking in conflicting_bookings]
        available_rooms = [r for r in eligible_rooms if r["_id"] not in booked_room_ids]
        
        if not available_rooms:
            return f"All rooms fitting {capacity} people are booked for {date} at {start_time}."
            
        best_room = available_rooms[0]
        return f"Room {best_room['name']} (capacity {best_room['capacity']}) is available."

@tool
async def book_room(date: str, start_time: str, end_time: str, capacity: int, organizer: str, description: str, room_name: str = None) -> str:
    """Book a room for a given date, start time, end time, minimum capacity, organizer, description, and optional room name.
    
    Args:
        date: The date in YYYY-MM-DD format.
        start_time: The start time in HH:MM format (24-hour).
        end_time: The end time in HH:MM format (24-hour).
        capacity: The number of people attending the meeting.
        organizer: The name of the person organizing the meeting.
        description: A short description or title of the meeting.
        room_name: (Optional) The specific name of the room to book.
        
    Returns:
        A formatted confirmation string if successful, or an error message if failed.
    """
    cursor = rooms_collection.find({"capacity": {"$gte": capacity}}).sort("capacity", 1)
    eligible_rooms = await cursor.to_list(length=100)

    if room_name:
        # Check specific room. Make regex flexible (e.g. '6a' or 'room 6a' matches 'Room-6A')
        clean_name = room_name.replace("Room ", "").replace("room ", "").replace("-", "")
        requested_room = await rooms_collection.find_one({"name": {"$regex": f"{clean_name}$", "$options": "i"}})
        if not requested_room:
            return f"Booking failed: Room {room_name} does not exist in our database."
        
        if requested_room["capacity"] < capacity:
            if not eligible_rooms:
                return f"Booking failed: Room {requested_room['name']} is a {requested_room['capacity']} seater room which is not available for {capacity} people."
            
            eligible_room_ids = [room["_id"] for room in eligible_rooms]
            conflicting_bookings_cursor = bookings_collection.find({
                "room_id": {"$in": eligible_room_ids},
                "date": date,
                "start_time": {"$lt": end_time},
                "end_time": {"$gt": start_time}
            })
            conflicting_bookings = await conflicting_bookings_cursor.to_list(length=100)
            booked_room_ids = [booking["room_id"] for booking in conflicting_bookings]
            available_rooms = [r for r in eligible_rooms if r["_id"] not in booked_room_ids]
            
            if available_rooms:
                alt_room = available_rooms[0]
                return f"Booking failed: Room {requested_room['name']} is a {requested_room['capacity']} seater room which is not available for {capacity} people. You can use {alt_room['name']} which can accommodate {capacity} people easily. Please confirm if you want to book this alternative room."
            else:
                return f"Booking failed: Room {requested_room['name']} is a {requested_room['capacity']} seater room which is not available for {capacity} people, and all other suitable rooms are currently booked."
        else:
            conflict = await bookings_collection.find_one({
                "room_id": requested_room["_id"],
                "date": date,
                "start_time": {"$lt": end_time},
                "end_time": {"$gt": start_time}
            })
            if conflict:
                return f"Booking failed: Room {requested_room['name']} is already booked at {start_time}."
            
            best_room = requested_room
            
    else:
        # Standard behaviour with no specific room
        if not eligible_rooms:
            return f"Booking failed: Room capacity is not enough. The requested capacity ({capacity} people) exceeds our largest available room."
            
        eligible_room_ids = [room["_id"] for room in eligible_rooms]
        
        conflicting_bookings_cursor = bookings_collection.find({
            "room_id": {"$in": eligible_room_ids},
            "date": date,
            "start_time": {"$lt": end_time},
            "end_time": {"$gt": start_time}
        })
        conflicting_bookings = await conflicting_bookings_cursor.to_list(length=100)
        
        booked_room_ids = [booking["room_id"] for booking in conflicting_bookings]
        available_rooms = [r for r in eligible_rooms if r["_id"] not in booked_room_ids]
        
        if not available_rooms:
            return f"Booking failed: No rooms available for {capacity} people on {date} at {start_time}."
            
        best_room = available_rooms[0]
    
    # 3. Create the booking
    booking_id = f"booking_{uuid.uuid4().hex[:8]}"
    
    booking_doc = {
        "_id": booking_id,
        "room_id": best_room["_id"],
        "date": date,
        "start_time": start_time,
        "end_time": end_time,
        "capacity": capacity,
        "organizer": organizer,
        "description": description,
        "booked_by": "user",
        "created_at": datetime.datetime.now(datetime.UTC)
    }
    
    try:
        await bookings_collection.insert_one(booking_doc)
        return (
            f"Your room has been booked.\n"
            f"Room: {best_room['name']}\n"
            f"Time: {date} {start_time} - {end_time}"
        )
    except Exception as e:
        # In case of race condition/duplicate key error
        return f"Booking failed due to a system error (possibly a double booking attempt)."

# System message to guide the agent
system_message = (
    "You are a helpful and efficient Room Booking Agent. "
    "Your goal is to help users check room availability and book meeting rooms. "
    f"Today's date is {datetime.datetime.now().strftime('%Y-%m-%d')}. "
    "IMPORTANT: Each user message will start with '[Logged-in user: NAME]'. "
    "Use this NAME as the meeting organizer automatically. Do NOT ask the user for their name or the organizer's name. "
    "Before booking, you MUST gather the following information:\n"
    "1. Date of the meeting\n"
    "2. Start time\n"
    "3. End time (or duration)\n"
    "4. Number of people attending\n"
    "5. A short description or title of the meeting\n"
    "If any of these details are missing, politely ask the user for them. "
    "If the user asks for a specific room by name (e.g., 'Room 6D' or '6D'), you MUST pass it to the `room_name` parameter of the tools. "
    "Once you have ALL the required information, ONLY THEN should you call the `book_room` tool. "
    "Only call `check_availability` if the user explicitly asks to check without booking. "
    "Be concise and friendly in your responses."
)

# Tools available to the agent
tools = [check_availability, book_room]

# Create memory saver for session persistence
memory = MemorySaver()

# Create the LangGraph agent
agent_executor = create_react_agent(llm, tools, prompt=system_message, checkpointer=memory)
