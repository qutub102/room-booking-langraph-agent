import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.schemas.schemas import ChatRequest, ChatResponse, CalendarResponse, RoomSchedule, BookingSchema, SignupRequest, LoginRequest, TokenResponse
from src.database.db import init_db, rooms_collection, bookings_collection, users_collection
from src.auth.auth import hash_password, verify_password, create_access_token
from src.agent.agent import agent_executor
import datetime


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the database on startup
    await init_db()
    yield
    # Cleanup on shutdown could go here

app = FastAPI(
    title="Room Booking Agent API",
    description="API for checking and booking meeting rooms via a conversational agent.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "https://room-booking-langraph-agent.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to the Room Booking Agent API!"}

@app.get("/calendar", response_model=CalendarResponse)
async def get_calendar(date: str = None):
    """
    Get all rooms and their bookings for a given date (defaults to today).
    """
    if not date:
        date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Fetch all rooms
    all_rooms = await rooms_collection.find().sort("capacity", 1).to_list(length=100)
    
    # Fetch all bookings for this date
    todays_bookings = await bookings_collection.find({"date": date}).to_list(length=100)
    
    # Group bookings by room_id
    bookings_by_room = {}
    for booking in todays_bookings:
        room_id = booking["room_id"]
        if room_id not in bookings_by_room:
            bookings_by_room[room_id] = []
        bookings_by_room[room_id].append(BookingSchema(
            room_id=booking["room_id"],
            date=booking["date"],
            start_time=booking["start_time"],
            end_time=booking.get("end_time", "Unknown"),
            organizer=booking.get("organizer", "Unknown")
        ))
    
    # Build schedules
    schedules = []
    for room in all_rooms:
        schedules.append(RoomSchedule(
            room_id=room["_id"],
            room_name=room["name"],
            capacity=room["capacity"],
            bookings=bookings_by_room.get(room["_id"], [])
        ))
    
    return CalendarResponse(date=date, schedules=schedules)

@app.post("/signup", response_model=TokenResponse)
async def signup(request: SignupRequest):
    """
    Register a new user.
    """
    existing = await users_collection.find_one({"email": request.email.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_doc = {
        "name": request.name,
        "email": request.email.lower(),
        "password": hash_password(request.password),
        "created_at": datetime.datetime.now(datetime.UTC)
    }
    await users_collection.insert_one(user_doc)
    
    token = create_access_token({"email": user_doc["email"], "name": user_doc["name"]})
    return TokenResponse(token=token, name=user_doc["name"])

@app.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    Authenticate a user and return a JWT token.
    """
    user = await users_collection.find_one({"email": request.email.lower()})
    if not user or not verify_password(request.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_access_token({"email": user["email"], "name": user["name"]})
    return TokenResponse(token=token, name=user["name"])

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Interact with the Room Booking Agent.
    """
    import os
    from dotenv import load_dotenv

    # Load environment variables before anything else
    load_dotenv()
    print("inside chat",os.getenv("OPENAI_API_KEY"))
    if not request.message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
        
    try:
        # Prepend the username context so agent knows the organizer
        augmented_message = f"[Logged-in user: {request.username}] {request.message}"
        config = {"configurable": {"thread_id": request.session_id}}
        result = await agent_executor.ainvoke(
            {"messages": [("user", augmented_message)]},
            config=config
        )
        
        # The result is a dict with "messages", where the last message is the AI's response
        final_response = result["messages"][-1].content
        
        return ChatResponse(response=final_response)
        
    except Exception as e:
        print(f"Error executing agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
