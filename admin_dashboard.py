from sqladmin import Admin, ModelView
from sqlalchemy import create_engine
from database import User, Room, Message, UserActivity

# Database URL - should match your main database
DATABASE_URL = "postgresql://postgres:suneel@localhost/chatapp"
engine = create_engine(DATABASE_URL)

# User Admin View
class UserAdmin(ModelView, model=User):
    column_list = ["id", "username", "email", "role", "is_active", "created_at", "last_login"]
    column_searchable_list = ["username", "email"]
    column_sortable_list = ["id", "username", "created_at", "last_login"]
    column_filters = ["role", "is_active"]
    form_excluded_columns = ["hashed_password", "messages", "rooms", "created_rooms"]
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True

class RoomAdmin(ModelView, model=Room):
    column_list = ["id", "name", "room_type", "creator_id", "is_active", "created_at"]
    column_searchable_list = ["name", "description"]
    column_sortable_list = ["id", "name", "created_at"]
    column_filters = ["room_type", "is_active"]
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True

class MessageAdmin(ModelView, model=Message):
    column_list = ["id", "content", "message_type", "room_id", "user_id", "created_at"]
    column_searchable_list = ["content"]
    column_sortable_list = ["id", "created_at"]
    column_filters = ["message_type", "is_deleted", "is_edited"]
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True

class UserActivityAdmin(ModelView, model=UserActivity):
    column_list = ["id", "user_id", "activity_type", "room_id", "created_at"]
    column_searchable_list = ["activity_type", "extra_metadata"]
    column_sortable_list = ["id", "created_at"]
    column_filters = ["activity_type"]
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True

# Register admin views
def setup_admin(app):
    admin = Admin(app, engine, title="Chat Application Admin")
    admin.add_view(UserAdmin)
    admin.add_view(RoomAdmin)
    admin.add_view(MessageAdmin)
    admin.add_view(UserActivityAdmin)
    # Optional: configure admin
    admin.templates_dir = "admin_templates"
    admin.statics_dir = "admin_static"
    admin.page_size = 20
    return admin

# Custom dashboard statistics
class DashboardStats:
    @staticmethod
    def get_user_stats():
        """Get user statistics for dashboard"""
        from sqlalchemy.orm import sessionmaker
        Session = sessionmaker(bind=engine)
        session = Session()
        try:
            total_users = session.query(User).count()
            active_users = session.query(User).filter(User.is_active == True).count()
            admin_users = session.query(User).filter(User.role == 'admin').count()
            return {
                'total_users': total_users,
                'active_users': active_users,
                'admin_users': admin_users
            }
        finally:
            session.close()
    
    @staticmethod
    def get_room_stats():
        """Get room statistics for dashboard"""
        from sqlalchemy.orm import sessionmaker
        Session = sessionmaker(bind=engine)
        session = Session()
        try:
            total_rooms = session.query(Room).count()
            active_rooms = session.query(Room).filter(Room.is_active == True).count()
            public_rooms = session.query(Room).filter(Room.room_type == 'public').count()
            private_rooms = session.query(Room).filter(Room.room_type == 'private').count()
            return {
                'total_rooms': total_rooms,
                'active_rooms': active_rooms,
                'public_rooms': public_rooms,
                'private_rooms': private_rooms
            }
        finally:
            session.close()
    
    @staticmethod
    def get_message_stats():
        """Get message statistics for dashboard"""
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy import func
        Session = sessionmaker(bind=engine)
        session = Session()
        try:
            total_messages = session.query(Message).count()
            today_messages = session.query(Message).filter(
                func.date(Message.created_at) == func.current_date()
            ).count()
            return {
                'total_messages': total_messages,
                'today_messages': today_messages
            }
        finally:
            session.close()

# Authentication middleware for admin 
class AdminAuth:
    @staticmethod
    def authenticate(request):
        """
        Custom authentication logic for admin access
        This is a basic example - implement proper authentication
        """
        # You would typically check session, JWT token, or other auth method
        # For now, this is a placeholder
        return True  # Replace with actual authentication logic
    
    @staticmethod
    def get_current_user(request):
        """Get current authenticated admin user"""
        # Return user info for admin interface
        return {"username": "admin", "role": "admin"}

__all__ = ['setup_admin', 'UserAdmin', 'RoomAdmin', 'MessageAdmin', 'UserActivityAdmin', 'DashboardStats']