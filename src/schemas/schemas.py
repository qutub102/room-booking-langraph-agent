from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default_session"
    username: str = "anonymous"

class SignupRequest(BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    token: str
    name: str

class ChatResponse(BaseModel):
    response: str

class BookingSchema(BaseModel):
    room_id: str
    date: str
    start_time: str
    end_time: str
    organizer: str

class RoomSchedule(BaseModel):
    room_id: str
    room_name: str
    capacity: int
    bookings: list[BookingSchema]

class CalendarResponse(BaseModel):
    date: str
    schedules: list[RoomSchedule]
