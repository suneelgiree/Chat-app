from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import timedelta, datetime
from typing import List, Optional
import json
import csv
import io
import pandas as pd

from database import get_db, User, Room, Message, UserActivity, user_room_association
from auth import (
    authenticate_user, create_access_token, get_current_user, 
    require_admin, require_user, get_password_hash, verify_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from models import (
    UserCreate, UserResponse, UserLogin, Token, RoomCreate, RoomResponse,
    MessageCreate, MessageResponse, RoomAnalytics, UserAnalytics, ActivityFilter
)
from websocket_manager import manager
from admin_dashboard import setup_admin

app = FastAPI(title="Advanced Chat Application", version="2.0.0")

# Setup admin dashboard (mounts /admin automatically)
setup_admin(app)

# Helper function to log user activity
def log_user_activity(db: Session, user_id: int, activity_type: str, room_id: Optional[int] = None, metadata: Optional[str] = None):
    activity = UserActivity(
        user_id=user_id,
        activity_type=activity_type,
        room_id=room_id,
        metadata=metadata
    )
    db.add(activity)
    db.commit()

# Authentication Routes
@app.post("/signup", response_model=UserResponse)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@app.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = authenticate_user(db, user.username, user.password)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    db_user.last_login = datetime.utcnow()
    db.commit()
    
    # Log login activity
    log_user_activity(db, db_user.id, "login")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.username, "role": db_user.role},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Room Management Routes
@app.post("/rooms", response_model=RoomResponse)
def create_room(room: RoomCreate, current_user: User = Depends(require_user), db: Session = Depends(get_db)):
    # Check if room already exists
    db_room = db.query(Room).filter(Room.name == room.name).first()
    if db_room:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Room name already exists"
        )
    
    # Create new room
    db_room = Room(
        name=room.name,
        description=room.description,
        room_type=room.room_type,
        creator_id=current_user.id
    )
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    
    # Add creator to room
    db_room.users.append(current_user)
    db.commit()
    
    # Log room creation
    log_user_activity(db, current_user.id, "create_room", db_room.id)
    
    return db_room

@app.get("/rooms", response_model=List[RoomResponse])
def get_rooms(current_user: User = Depends(require_user), db: Session = Depends(get_db)):
    rooms = db.query(Room).filter(Room.is_active == True).all()
    
    # Add message and user counts
    room_responses = []
    for room in rooms:
        message_count = db.query(Message).filter(
            Message.room_id == room.id,
            Message.is_deleted == False
        ).count()
        
        user_count = db.query(user_room_association).filter(
            user_room_association.c.room_id == room.id
        ).count()
        
        room_response = RoomResponse(
            id=room.id,
            name=room.name,
            description=room.description,
            room_type=room.room_type,
            creator_id=room.creator_id,
            is_active=room.is_active,
            created_at=room.created_at,
            message_count=message_count,
            user_count=user_count
        )
        room_responses.append(room_response)
    
    return room_responses

@app.post("/rooms/{room_id}/join")
def join_room(room_id: int, current_user: User = Depends(require_user), db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Check if user is already in room
    if current_user in room.users:
        raise HTTPException(status_code=400, detail="Already joined this room")
    
    # Add user to room
    room.users.append(current_user)
    db.commit()
    
    # Log join activity
    log_user_activity(db, current_user.id, "join_room", room_id)
    
    return {"message": f"Successfully joined room {room.name}"}

# Message Routes
@app.get("/rooms/{room_id}/messages", response_model=List[MessageResponse])
def get_messages(
    room_id: int,
    cursor: Optional[int] = Query(None),
    limit: int = Query(50, le=100),
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    # Check if user has access to room
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    if current_user not in room.users and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied to this room")
    
    query = db.query(Message).filter(
        Message.room_id == room_id,
        Message.is_deleted == False
    )
    
    if cursor:
        query = query.filter(Message.id < cursor)
    
    messages = query.order_by(Message.id.desc()).limit(limit).all()
    
    # Convert to response format
    message_responses = []
    for message in messages:
        message_responses.append(MessageResponse(
            id=message.id,
            content=message.content,
            message_type=message.message_type,
            room_id=message.room_id,
            user_id=message.user_id,
            username=message.user.username,
            is_edited=message.is_edited,
            is_deleted=message.is_deleted,
            created_at=message.created_at,
            edited_at=message.edited_at
        ))
    
    return message_responses

# Analytics Routes (Admin Only)
@app.get("/analytics/rooms", response_model=List[RoomAnalytics])
def get_room_analytics(
    filters: ActivityFilter = Depends(),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    query = db.query(Room).filter(Room.is_active == True)
    
    analytics = []
    for room in query.all():
        message_query = db.query(Message).filter(
            Message.room_id == room.id,
            Message.is_deleted == False
        )
        
        if filters.start_date:
            message_query = message_query.filter(Message.created_at >= filters.start_date)
        if filters.end_date:
            message_query = message_query.filter(Message.created_at <= filters.end_date)
        
        message_count = message_query.count()
        user_count = len(room.users)
        
        last_message = message_query.order_by(Message.created_at.desc()).first()
        last_activity = last_message.created_at if last_message else None
        
        analytics.append(RoomAnalytics(
            room_id=room.id,
            room_name=room.name,
            message_count=message_count,
            user_count=user_count,
            last_activity=last_activity
        ))
    
    return analytics

@app.get("/analytics/users", response_model=List[UserAnalytics])
def get_user_analytics(
    filters: ActivityFilter = Depends(),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    query = db.query(User).filter(User.is_active == True)
    
    analytics = []
    for user in query.all():
        message_query = db.query(Message).filter(
            Message.user_id == user.id,
            Message.is_deleted == False
        )
        
        if filters.start_date:
            message_query = message_query.filter(Message.created_at >= filters.start_date)
        if filters.end_date:
            message_query = message_query.filter(Message.created_at <= filters.end_date)
        
        message_count = message_query.count()
        rooms_joined = len(user.rooms)
        
        last_activity_query = db.query(UserActivity).filter(
            UserActivity.user_id == user.id
        ).order_by(UserActivity.timestamp.desc()).first()
        
        last_activity = last_activity_query.timestamp if last_activity_query else None
        
        analytics.append(UserAnalytics(
            user_id=user.id,
            username=user.username,
            message_count=message_count,
            rooms_joined=rooms_joined,
            last_activity=last_activity
        ))
    
    return analytics

# CSV Export Routes
@app.get("/analytics/export/rooms")
def export_room_analytics(
    format: str = Query("csv", enum=["csv", "xlsx"]),
    filters: ActivityFilter = Depends(),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    # Get room analytics data
    analytics_data = []
    query = db.query(Room).filter(Room.is_active == True)
    
    for room in query.all():
        message_query = db.query(Message).filter(
            Message.room_id == room.id,
            Message.is_deleted == False
        )
        
        if filters.start_date:
            message_query = message_query.filter(Message.created_at >= filters.start_date)
        if filters.end_date:
            message_query = message_query.filter(Message.created_at <= filters.end_date)
        
        message_count = message_query.count()
        user_count = len(room.users)
        
        last_message = message_query.order_by(Message.created_at.desc()).first()
        last_activity = last_message.created_at.isoformat() if last_message else ""
        
        analytics_data.append({
            "room_id": room.id,
            "room_name": room.name,
            "room_type": room.room_type,
            "message_count": message_count,
            "user_count": user_count,
            "created_at": room.created_at.isoformat(),
            "last_activity": last_activity
        })
    
    if format == "csv":
        # Create CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=analytics_data[0].keys())
        writer.writeheader()
        writer.writerows(analytics_data)
        output.seek(0)
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=room_analytics.csv"}
        )
    
    elif format == "xlsx":
        # Create Excel file
        df = pd.DataFrame(analytics_data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Room Analytics', index=False)
        output.seek(0)
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=room_analytics.xlsx"}
        )

@app.get("/analytics/export/users")
def export_user_analytics(
    format: str = Query("csv", enum=["csv", "xlsx"]),
    filters: ActivityFilter = Depends(),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    # Get user analytics data
    analytics_data = []
    query = db.query(User).filter(User.is_active == True)
    
    for user in query.all():
        message_query = db.query(Message).filter(
            Message.user_id == user.id,
            Message.is_deleted == False
        )
        
        if filters.start_date:
            message_query = message_query.filter(Message.created_at >= filters.start_date)
        if filters.end_date:
            message_query = message_query.filter(Message.created_at <= filters.end_date)
        
        message_count = message_query.count()
        rooms_joined = len(user.rooms)
        
        last_activity_query = db.query(UserActivity).filter(
            UserActivity.user_id == user.id
        ).order_by(UserActivity.timestamp.desc()).first()
        
        last_activity = last_activity_query.timestamp.isoformat() if last_activity_query else ""
        
        analytics_data.append({
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "message_count": message_count,
            "rooms_joined": rooms_joined,
            "created_at": user.created_at.isoformat(),
            "last_login": user.last_login.isoformat(),
            "last_activity": last_activity
        })
    
    if format == "csv":
        # Create CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=analytics_data[0].keys())
        writer.writeheader()
        writer.writerows(analytics_data)
        output.seek(0)
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=user_analytics.csv"}
        )
    
    elif format == "xlsx":
        # Create Excel file
        df = pd.DataFrame(analytics_data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='User Analytics', index=False)
        output.seek(0)
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=user_analytics.xlsx"}
        )

# Enhanced WebSocket Chat Endpoint
@app.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: int,
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    try:
        # Verify JWT token
        token_data = verify_token(token)
        user = db.query(User).filter(User.username == token_data["username"]).first()
        
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Check if room exists and user has access
        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Auto-join room if user is not already in it
        if user not in room.users:
            room.users.append(user)
            db.commit()
            log_user_activity(db, user.id, "join_room", room_id)
        
        # Connect to room
        await manager.connect(websocket, str(room_id))
        
        # Send recent messages (last 50)
        recent_messages = db.query(Message).filter(
            Message.room_id == room_id,
            Message.is_deleted == False
        ).order_by(Message.id.desc()).limit(50).all()
        
        for message in reversed(recent_messages):
            message_data = {
                "id": message.id,
                "content": message.content,
                "message_type": message.message_type,
                "room_id": message.room_id,
                "user_id": message.user_id,
                "username": message.user.username,
                "created_at": message.created_at.isoformat(),
                "type": "history"
            }
            await manager.send_personal_message(json.dumps(message_data), websocket)
        
        # Listen for new messages
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Save message to database
            new_message = Message(
                content=message_data["content"],
                message_type=message_data.get("message_type", "text"),
                room_id=room_id,
                user_id=user.id
            )
            db.add(new_message)
            db.commit()
            db.refresh(new_message)
            
            # Log message activity
            log_user_activity(db, user.id, "send_message", room_id)
            
            # Broadcast to all clients in the room
            broadcast_data = {
                "id": new_message.id,
                "content": new_message.content,
                "message_type": new_message.message_type,
                "room_id": room_id,
                "user_id": user.id,
                "username": user.username,
                "created_at": new_message.created_at.isoformat(),
                "type": "new_message"
            }
            
            await manager.broadcast_to_room(broadcast_data, str(room_id))
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, str(room_id))
    except Exception as e:
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        manager.disconnect(websocket, str(room_id))

# Protected Routes
@app.get("/users/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.get("/admin/users", response_model=List[UserResponse])
def get_all_users(current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

# Health check endpoint
@app.get("/")
def read_root():
    return {"message": "Advanced Chat Application API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)