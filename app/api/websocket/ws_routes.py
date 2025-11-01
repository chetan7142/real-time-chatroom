import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.api.deps import get_current_user_ws
from app.api.websocket.chat_manager import manager
from app.services.message_service import create_message
from app.services.room_service import user_is_room_member
from app.db.session import AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.websocket('/rooms/{room_id}')
async def websocket_endpoint(websocket: WebSocket, room_id: int):
    """WebSocket endpoint for real-time chat in a room
    
    Token can be passed as:
    - Query parameter: ?token=xxx
    - Authorization header: Authorization: Bearer xxx
    """
    db: AsyncSession = None
    try:
        # Get token from query params or headers (before accepting)
        token = None
        query_params = dict(websocket.query_params)
        token = query_params.get('token')
        
        if not token:
            # Try Authorization header
            headers = dict(websocket.headers)
            auth_header = headers.get('authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header.replace('Bearer ', '')
        
        # Authenticate user
        user = await get_current_user_ws(token)
        if not user:
            await websocket.accept()
            await websocket.close(code=1008, reason="Authentication required")
            return
        
        # Get database session
        db = AsyncSessionLocal()
        
        # Check if user is a member of the room
        is_member = await user_is_room_member(db, room_id, user.id)
        if not is_member:
            await db.close()
            await websocket.accept()
            await websocket.close(code=1008, reason="Access denied")
            return
        
        # Connect to room (this will accept the connection)
        await manager.connect(room_id, websocket, user.id)
        
        try:
            while True:
                data = await websocket.receive_json()
                await handle_websocket_message(room_id, user.id, data, db)
                
        except WebSocketDisconnect:
            logger.info(f"User {user.id} disconnected from room {room_id}")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            await manager.disconnect(room_id, websocket)
            if db:
                await db.close()
            
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        if db:
            await db.close()
        await websocket.close(code=1011, reason="Internal server error")

async def handle_websocket_message(room_id: int, user_id: int, data: dict, db: AsyncSession):
    """Handle incoming WebSocket messages"""
    message_type = data.get("type")
    
    if message_type == "message":
        # Handle chat message
        content = data.get("content", "").strip()
        if content:
            try:
                # Create message in database
                from app.schemas.message import MessageCreate
                message_data = MessageCreate(
                    content=content,
                    mentions=data.get("mentions", [])
                )
                message = await create_message(db, message_data, room_id, user_id)
                
                # Broadcast to room
                await manager.broadcast_to_room(room_id, {
                    "type": "message",
                    "message": {
                        "id": message.id,
                        "room_id": message.room_id,
                        "user_id": message.user_id,
                        "content": message.content,
                        "created_at": message.created_at.isoformat(),
                        "edited_at": message.edited_at.isoformat() if message.edited_at else None,
                        "is_deleted": message.is_deleted
                    },
                    "temp_id": data.get("temp_id")  # For optimistic UI updates
                })
                
            except Exception as e:
                logger.error(f"Error creating message: {e}")
                await manager.send_to_user(user_id, {
                    "type": "error",
                    "message": "Failed to send message"
                })
    
    elif message_type == "typing":
        # Handle typing indicator
        await manager.broadcast_to_room(room_id, {
            "type": "typing",
            "user_id": user_id,
            "is_typing": data.get("is_typing", False)
        })
    
    elif message_type == "ping":
        # Handle ping/pong for connection health
        await manager.send_to_user(user_id, {
            "type": "pong"
        })
    
    else:
        logger.warning(f"Unknown message type: {message_type}")

# Redis will be initialized when app starts (see main.py)
