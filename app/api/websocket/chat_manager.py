import json
import asyncio
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
from app.core.redis import get_redis
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # room_id -> set of websockets
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # user_id -> set of websockets (for presence tracking)
        self.user_connections: Dict[int, Set[WebSocket]] = {}
        # websocket -> user_id mapping
        self.websocket_users: Dict[WebSocket, int] = {}
        self.redis = None
        self.pubsub = None
        self.redis_task = None

    async def initialize_redis(self):
        """Initialize Redis connection and start listening for messages"""
        self.redis = await get_redis()
        self.pubsub = self.redis.pubsub()
        # Subscribe to all room channels
        await self.pubsub.psubscribe("room:*")
        # Start background task to process Redis messages
        self.redis_task = asyncio.create_task(self._process_redis_messages())

    async def _process_redis_messages(self):
        """Process messages from Redis Pub/Sub"""
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "pmessage":
                    # Extract room_id from pattern "room:*"
                    channel = message.get("channel", "")
                    if "room:" in channel:
                        room_id_str = channel.replace("room:", "")
                        try:
                            room_id = int(room_id_str)
                            data = json.loads(message["data"])
                            await self._broadcast_to_room(room_id, data)
                        except (ValueError, json.JSONDecodeError) as e:
                            logger.error(f"Error processing Redis message: {e}")
        except asyncio.CancelledError:
            logger.info("Redis message processing cancelled")
        except Exception as e:
            logger.error(f"Error processing Redis messages: {e}")

    async def connect(self, room_id: int, websocket: WebSocket, user_id: int = None):
        """Connect a WebSocket to a room"""
        await websocket.accept()
        
        if room_id not in self.active_connections:
            self.active_connections[room_id] = set()
        
        self.active_connections[room_id].add(websocket)
        
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(websocket)
            self.websocket_users[websocket] = user_id
            
            # Notify room about user joining
            await self._publish_to_room(room_id, {
                "type": "user_joined",
                "user_id": user_id,
                "room_id": room_id
            })

    async def disconnect(self, room_id: int, websocket: WebSocket):
        """Disconnect a WebSocket from a room"""
        if room_id in self.active_connections:
            self.active_connections[room_id].discard(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
        
        # Remove from user connections
        user_id = self.websocket_users.get(websocket)
        if user_id:
            if user_id in self.user_connections:
                self.user_connections[user_id].discard(websocket)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            
            # Notify room about user leaving before removing the mapping
            await self._publish_to_room(room_id, {
                "type": "user_left",
                "user_id": user_id,
                "room_id": room_id
            })
            
            del self.websocket_users[websocket]

    async def _broadcast_to_room(self, room_id: int, message: dict):
        """Broadcast message to all WebSockets in a room"""
        if room_id in self.active_connections:
            disconnected = set()
            for ws in self.active_connections[room_id]:
                try:
                    await ws.send_json(message)
                except WebSocketDisconnect:
                    disconnected.add(ws)
                except Exception as e:
                    logger.error(f"Error sending message to WebSocket: {e}")
                    disconnected.add(ws)
            
            # Clean up disconnected WebSockets
            for ws in disconnected:
                self.active_connections[room_id].discard(ws)

    async def _publish_to_room(self, room_id: int, message: dict):
        """Publish message to Redis channel for the room"""
        if self.redis:
            try:
                await self.redis.publish(f"room:{room_id}", json.dumps(message))
            except Exception as e:
                logger.error(f"Error publishing to Redis: {e}")

    async def broadcast_to_room(self, room_id: int, message: dict):
        """Broadcast message to a room (publishes to Redis)"""
        await self._publish_to_room(room_id, message)

    async def send_to_user(self, user_id: int, message: dict):
        """Send message to all WebSockets of a specific user"""
        if user_id in self.user_connections:
            disconnected = set()
            for ws in self.user_connections[user_id]:
                try:
                    await ws.send_json(message)
                except WebSocketDisconnect:
                    disconnected.add(ws)
                except Exception as e:
                    logger.error(f"Error sending message to user WebSocket: {e}")
                    disconnected.add(ws)
            
            # Clean up disconnected WebSockets
            for ws in disconnected:
                self.user_connections[user_id].discard(ws)

    async def get_room_users(self, room_id: int) -> List[int]:
        """Get list of user IDs currently in a room"""
        if room_id not in self.active_connections:
            return []
        
        users = set()
        for ws in self.active_connections[room_id]:
            user_id = self.websocket_users.get(ws)
            if user_id:
                users.add(user_id)
        return list(users)

    async def cleanup(self):
        """Clean up resources"""
        if self.redis_task:
            self.redis_task.cancel()
        if self.pubsub:
            await self.pubsub.close()
        if self.redis:
            await self.redis.close()

manager = ConnectionManager()
