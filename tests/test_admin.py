from fastapi import FastAPI
from sqladmin import Admin, ModelView
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import uvicorn

# For testing purposes, using SQLite instead of PostgreSQL
DATABASE_URL = "sqlite:///./test_chat.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

Base = declarative_base()

# Test Models (simplified versions)
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    role = Column(String(20), default="user")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    messages = relationship("Message", back_populates="user")
    created_rooms = relationship("Room", back_populates="creator")

class Room(Base):
    __tablename__ = "rooms"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)
    description = Column(Text, nullable=True)
    room_type = Column(String(20), default="public")
    creator_id = Column(Integer, ForeignKey("users.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    creator = relationship("User", back_populates="created_rooms")
    messages = relationship("Message", back_populates="room")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    message_type = Column(String(20), default="text")
    room_id = Column(Integer, ForeignKey("rooms.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    is_deleted = Column(Boolean, default=False)
    is_edited = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    room = relationship("Room", back_populates="messages")
    user = relationship("User", back_populates="messages")

class UserActivity(Base):
    __tablename__ = "user_activities"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    activity_type = Column(String(50))
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(title="Chat App with Admin")

# Create admin instance
admin = Admin(app, engine, title="Chat Application Admin")

# Admin Views
class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.username, User.email, User.role, User.is_active, User.created_at]
    column_searchable_list = [User.username, User.email]
    column_sortable_list = [User.id, User.username, User.created_at]
    column_filters = [User.role, User.is_active]
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True

class RoomAdmin(ModelView, model=Room):
    column_list = [Room.id, Room.name, Room.room_type, Room.creator_id, Room.is_active, Room.created_at]
    column_searchable_list = [Room.name, Room.description]
    column_sortable_list = [Room.id, Room.name, Room.created_at]
    column_filters = [Room.room_type, Room.is_active]
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True

class MessageAdmin(ModelView, model=Message):
    column_list = [Message.id, Message.content, Message.message_type, Message.room_id, Message.user_id, Message.created_at]
    column_searchable_list = [Message.content]
    column_sortable_list = [Message.id, Message.created_at]
    column_filters = [Message.message_type, Message.is_deleted, Message.is_edited]
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True

class UserActivityAdmin(ModelView, model=UserActivity):
    column_list = [
        UserActivity.id,
        UserActivity.user_id,
        UserActivity.activity_type,
        UserActivity.room_id,
        UserActivity.timestamp 
    ]
    column_searchable_list = [
        UserActivity.activity_type,
        UserActivity.extra_metadata
    ]
    column_sortable_list = [
        UserActivity.id,
        UserActivity.timestamp  # or .created_at
    ]
    column_filters = [UserActivity.activity_type]
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True

# Register admin views
admin.add_view(UserAdmin)
admin.add_view(RoomAdmin)
admin.add_view(MessageAdmin)
admin.add_view(UserActivityAdmin)

# Test API endpoints
@app.get("/")
async def root():
    return {"message": "Chat Application is running! Visit /admin for admin panel"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "admin_url": "/admin"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)