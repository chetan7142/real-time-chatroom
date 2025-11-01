import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import auth, users, rooms, messages, files, notifications
from app.api.websocket.ws_routes import router as ws_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Real-Time Collaboration Platform API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(rooms.router, prefix=f"{settings.API_V1_STR}/rooms", tags=["rooms"])
app.include_router(messages.router, prefix=f"{settings.API_V1_STR}/messages", tags=["messages"])
app.include_router(files.router, prefix=f"{settings.API_V1_STR}/files", tags=["files"])
app.include_router(notifications.router, prefix=f"{settings.API_V1_STR}/notifications", tags=["notifications"])

# WebSocket routes are mounted separately (they may not use the same prefix)
app.include_router(ws_router, prefix="/ws", tags=["websocket"])

@app.get('/')
async def root():
    return {'message': 'Real-Time Collaboration Platform API'}

if __name__ == '__main__':
    uvicorn.run('app.main:app', host='0.0.0.0', port=8000, reload=True)
