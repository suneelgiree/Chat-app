from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Query
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List, Optional
import json

from database import get_db, User, Message
from auth import (
    authenticate_user, create_access_token, get_current_user, 
    require_admin, require_user, get_password_hash, verify_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from models import UserCreate, UserResponse, UserLogin, Token, MessageCreate, MessageResponse
from websocket_manager import manager

app = FastAPI(title="Chat Application", version="1.0.0")

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
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.username, "role": db_user.role},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Protected Routes
@app.get("/users/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.get("/admin/users", response_model=List[UserResponse])
def get_all_users(current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

@app.get("/messages/{room_id}", response_model=List[MessageResponse])
def get_messages(
    room_id: str,
    cursor: Optional[int] = Query(None),
    limit: int = Query(50, le=100),
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    query = db.query(Message).filter(Message.room_id == room_id)
    
    if cursor:
        query = query.filter(Message.id < cursor)
    
    messages = query.order_by(Message.id.desc()).limit(limit).all()
    
    # Convert to response format
    message_responses = []
    for message in messages:
        message_responses.append(MessageResponse(
            id=message.id,
            content=message.content,
            room_id=message.room_id,
            user_id=message.user_id,
            username=message.user.username,
            created_at=message.created_at
        ))
    
    return message_responses

# WebSocket Chat Endpoint
@app.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: str,
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
        
        # Connect to room
        await manager.connect(websocket, room_id)
        
        # Send recent messages (last 50)
        recent_messages = db.query(Message).filter(
            Message.room_id == room_id
        ).order_by(Message.id.desc()).limit(50).all()
        
        for message in reversed(recent_messages):
            message_data = {
                "id": message.id,
                "content": message.content,
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
                room_id=room_id,
                user_id=user.id
            )
            db.add(new_message)
            db.commit()
            db.refresh(new_message)
            
            # Broadcast to all clients in the room
            broadcast_data = {
                "id": new_message.id,
                "content": new_message.content,
                "room_id": room_id,
                "user_id": user.id,
                "username": user.username,
                "created_at": new_message.created_at.isoformat(),
                "type": "new_message"
            }
            
            await manager.broadcast_to_room(broadcast_data, room_id)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
    except Exception as e:
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        manager.disconnect(websocket, room_id)

# Health check endpoint
@app.get("/")
def read_root():
    return {"message": "Chat Application API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)