from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
from enum import Enum

class RoleEnum(str, Enum):
    admin = "admin"
    user = "user"

class MessageTypeEnum(str, Enum):
    text = "text"
    image = "image"
    file = "file"
    system = "system"

class RoomTypeEnum(str, Enum):
    public = "public"
    private = "private"
    direct = "direct"

# User Models
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: Optional[RoleEnum] = RoleEnum.user

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime
    last_login: datetime

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Room Models
class RoomCreate(BaseModel):
    name: str
    description: Optional[str] = None
    room_type: Optional[RoomTypeEnum] = RoomTypeEnum.public

class RoomResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    room_type: str
    creator_id: int
    is_active: bool
    created_at: datetime
    message_count: Optional[int] = 0
    user_count: Optional[int] = 0

    class Config:
        from_attributes = True

# Message Models
class MessageCreate(BaseModel):
    content: str
    message_type: Optional[MessageTypeEnum] = MessageTypeEnum.text

class MessageResponse(BaseModel):
    id: int
    content: str
    message_type: str
    room_id: int
    user_id: int
    username: str
    is_edited: bool
    is_deleted: bool
    created_at: datetime
    edited_at: Optional[datetime]

    class Config:
        from_attributes = True

# Analytics Models
class RoomAnalytics(BaseModel):
    room_id: int
    room_name: str
    message_count: int
    user_count: int
    last_activity: Optional[datetime]

class UserAnalytics(BaseModel):
    user_id: int
    username: str
    message_count: int
    rooms_joined: int
    last_activity: Optional[datetime]

class ActivityFilter(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    room_id: Optional[int] = None
    user_id: Optional[int] = None