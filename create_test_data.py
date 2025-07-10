from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timedelta
import random

# Database configuration 
DATABASE_URL = "sqlite:///./test_chat.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

Base = declarative_base()

# Models 
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

def create_sample_data():
    """Create sample data for testing"""
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Check if data already exists
        if db.query(User).count() > 0:
            print("Sample data already exists. Skipping creation.")
            return
        
        print("Creating sample data...")
        
        # Create sample users
        users = [
            User(username="admin", email="admin@example.com", role="admin", 
                 last_login=datetime.utcnow() - timedelta(hours=1)),
            User(username="john_doe", email="john@example.com", role="user", 
                 last_login=datetime.utcnow() - timedelta(hours=2)),
            User(username="jane_smith", email="jane@example.com", role="moderator", 
                 last_login=datetime.utcnow() - timedelta(hours=3)),
            User(username="bob_wilson", email="bob@example.com", role="user", 
                 last_login=datetime.utcnow() - timedelta(days=1)),
            User(username="alice_brown", email="alice@example.com", role="user", 
                 last_login=datetime.utcnow() - timedelta(days=2)),
        ]
        
        for user in users:
            db.add(user)
        db.commit()
        print(f" Created {len(users)} users")
        
        # Create sample rooms
        rooms = [
            Room(name="General Chat", description="General discussion room", 
                 room_type="public", creator_id=1),
            Room(name="Tech Talk", description="Technology discussions", 
                 room_type="public", creator_id=2),
            Room(name="Private Room", description="Private discussion", 
                 room_type="private", creator_id=3),
            Room(name="Gaming", description="Gaming discussions", 
                 room_type="public", creator_id=4),
            Room(name="Off Topic", description="Random discussions", 
                 room_type="public", creator_id=1),
        ]
        
        for room in rooms:
            db.add(room)
        db.commit()
        print(f" Created {len(rooms)} rooms")
        
        # Create sample messages
        messages = [
            Message(content="Welcome to the chat! Please be respectful.", 
                   message_type="text", room_id=1, user_id=1),
            Message(content="Hello everyone! Great to be here.", 
                   message_type="text", room_id=1, user_id=2),
            Message(content="How's everyone doing today?", 
                   message_type="text", room_id=1, user_id=3),
            Message(content="Great to be here! Looking forward to discussions.", 
                   message_type="text", room_id=2, user_id=4),
            Message(content="Let's discuss the latest tech trends and innovations.", 
                   message_type="text", room_id=2, user_id=2),
            Message(content="Anyone playing the new game that came out?", 
                   message_type="text", room_id=4, user_id=5),
            Message(content="I'm excited about the new AI developments.", 
                   message_type="text", room_id=2, user_id=1),
            Message(content="What are your thoughts on the latest updates?", 
                   message_type="text", room_id=5, user_id=3),
            Message(content="This is a private message for testing.", 
                   message_type="text", room_id=3, user_id=3),
            Message(content="Anyone here interested in collaboration?", 
                   message_type="text", room_id=1, user_id=4),
        ]
        
        for message in messages:
            db.add(message)
        db.commit()
        print(f" Created {len(messages)} messages")
        
        # Create sample user activities
        activities = [
            UserActivity(user_id=1, activity_type="login", 
                        details="Admin logged in from web interface"),
            UserActivity(user_id=2, activity_type="join_room", room_id=1, 
                        details="Joined General Chat room"),
            UserActivity(user_id=3, activity_type="create_room", room_id=3, 
                        details="Created Private Room"),
            UserActivity(user_id=4, activity_type="send_message", room_id=4, 
                        details="Sent message in Gaming room"),
            UserActivity(user_id=5, activity_type="login", 
                        details="User logged in from mobile app"),
            UserActivity(user_id=1, activity_type="create_room", room_id=5, 
                        details="Created Off Topic room"),
            UserActivity(user_id=2, activity_type="send_message", room_id=2, 
                        details="Sent message in Tech Talk"),
            UserActivity(user_id=3, activity_type="edit_profile", 
                        details="Updated user profile information"),
            UserActivity(user_id=4, activity_type="logout", 
                        details="User logged out"),
            UserActivity(user_id=5, activity_type="join_room", room_id=4, 
                        details="Joined Gaming room"),
        ]
        
        for activity in activities:
            db.add(activity)
        db.commit()
        print(f" Created {len(activities)} user activities")
        
        print("\n Sample data created successfully!")
        print("\nSummary:")
        print(f"- Users: {db.query(User).count()}")
        print(f"- Rooms: {db.query(Room).count()}")
        print(f"- Messages: {db.query(Message).count()}")
        print(f"- User Activities: {db.query(UserActivity).count()}")
        
        print("\n Now you can:")
        print("1. Start your admin server: python test_admin.py")
        print("2. Visit: http://localhost:8000/admin")
        print("3. Test all the CRUD operations!")
        
    except Exception as e:
        print(f" Error creating sample data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def clear_sample_data():
    """Clear all sample data from database"""
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Delete in reverse order to avoid foreign key constraints
        db.query(UserActivity).delete()
        db.query(Message).delete()
        db.query(Room).delete()
        db.query(User).delete()
        db.commit()
        print(" All sample data cleared!")
        
    except Exception as e:
        print(f" Error clearing sample data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "clear":
        clear_sample_data()
    else:
        create_sample_data()