from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import sys
import os

# Database configuration - must match your main application
DATABASE_URL = "sqlite:///./test_chat.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

Base = declarative_base()

# Models (must match your main application models)
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

def test_database_connection():
    """Test database connection and basic operations"""
    print("🔍 Testing Database Connection...")
    
    try:
        # Test connection
        connection = engine.connect()
        connection.close()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_database_queries():
    """Test database operations and data integrity"""
    print("\n🔍 Testing Database Queries...")
    
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Test basic counts
        user_count = db.query(User).count()
        room_count = db.query(Room).count()
        message_count = db.query(Message).count()
        activity_count = db.query(UserActivity).count()
        
        print(f"📊 Database Statistics:")
        print(f"   Users: {user_count}")
        print(f"   Rooms: {room_count}")
        print(f"   Messages: {message_count}")
        print(f"   Activities: {activity_count}")
        
        if user_count == 0:
            print("⚠️  No users found. Run 'python create_test_data.py' first!")
            return False
        
        # Test relationships
        print(f"\n🔗 Testing Relationships:")
        
        # Test User-Message relationship
        user = db.query(User).first()
        if user:
            user_messages = len(user.messages)
            print(f"   User '{user.username}' has {user_messages} messages")
        
        # Test User-Room relationship
        user_rooms = len(user.created_rooms) if user else 0
        print(f"   User '{user.username}' created {user_rooms} rooms")
        
        # Test Room-Message relationship
        room = db.query(Room).first()
        if room:
            room_messages = len(room.messages)
            print(f"   Room '{room.name}' has {room_messages} messages")
            print(f"   Room creator: {room.creator.username if room.creator else 'None'}")
        
        # Test data integrity
        print(f"\n🔍 Testing Data Integrity:")
        
        # Check for orphaned messages
        orphaned_messages = db.query(Message).filter(
            ~Message.user_id.in_(db.query(User.id))
        ).count()
        print(f"   Orphaned messages: {orphaned_messages}")
        
        # Check for orphaned rooms
        orphaned_rooms = db.query(Room).filter(
            ~Room.creator_id.in_(db.query(User.id))
        ).count()
        print(f"   Orphaned rooms: {orphaned_rooms}")
        
        # Check for orphaned activities
        orphaned_activities = db.query(UserActivity).filter(
            ~UserActivity.user_id.in_(db.query(User.id))
        ).count()
        print(f"   Orphaned activities: {orphaned_activities}")
        
        if orphaned_messages == 0 and orphaned_rooms == 0 and orphaned_activities == 0:
            print("✅ Data integrity check passed")
        else:
            print("⚠️  Data integrity issues found")
        
        return True
        
    except Exception as e:
        print(f"❌ Database query test failed: {e}")
        return False
    finally:
        db.close()

def test_admin_models():
    """Test admin model configurations"""
    print("\n🔍 Testing Admin Model Configurations...")
    
    try:
        # Test model attributes
        models = [User, Room, Message, UserActivity]
        
        for model in models:
            print(f"   Testing {model.__name__}:")
            
            # Check if model has required attributes
            if hasattr(model, '__tablename__'):
                print(f"     ✅ Table name: {model.__tablename__}")
            else:
                print(f"     ❌ Missing table name")
                
            # Check primary key
            pk_columns = [col for col in model.__table__.columns if col.primary_key]
            if pk_columns:
                print(f"     ✅ Primary key: {pk_columns[0].name}")
            else:
                print(f"     ❌ No primary key found")
        
        print("✅ Admin model configuration test passed")
        return True
        
    except Exception as e:
        print(f"❌ Admin model test failed: {e}")
        return False

def test_file_existence():
    """Test if required files exist"""
    print("\n🔍 Testing File Existence...")
    
    required_files = [
        'test_admin.py',
        'create_test_data.py',
        'test_chat.db'
    ]
    
    all_exist = True
    for file in required_files:
        if os.path.exists(file):
            print(f"   ✅ {file} exists")
        else:
            print(f"   ❌ {file} missing")
            all_exist = False
    
    return all_exist

def run_comprehensive_test():
    """Run all tests"""
    print("🚀 Running Comprehensive Admin Dashboard Tests")
    print("=" * 50)
    
    tests = [
        ("File Existence", test_file_existence),
        ("Database Connection", test_database_connection),
        ("Database Queries", test_database_queries),
        ("Admin Models", test_admin_models),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
    
    print("\n" + "=" * 50)
    print(f"🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your admin dashboard is ready!")
        print("\n📋 Next steps:")
        print("1. Make sure test_admin.py is running: python test_admin.py")
        print("2. Open your browser: http://localhost:8000/admin")
        print("3. Test the admin interface manually")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        
        if not os.path.exists('test_chat.db'):
            print("\n💡 Quick fix: Run 'python create_test_data.py' first!")
    
    return passed == total

def show_admin_urls():
    """Show available admin URLs"""
    print("\n🌐 Available Admin URLs:")
    print("   Main app: http://localhost:8000/")
    print("   Admin panel: http://localhost:8000/admin")
    print("   Health check: http://localhost:8000/health")
    print("\n📱 Manual Testing Checklist:")
    print("   □ Open admin panel in browser")
    print("   □ Check all 4 model views (Users, Rooms, Messages, Activities)")
    print("   □ Test creating a new user")
    print("   □ Test editing a user")
    print("   □ Test search functionality")
    print("   □ Test filter functionality")
    print("   □ Test deleting a record")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "urls":
        show_admin_urls()
    else:
        success = run_comprehensive_test()
        if success:
            show_admin_urls()