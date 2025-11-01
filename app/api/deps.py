from fastapi import Depends, HTTPException, status, WebSocket
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.services.user_service import get_user_by_id
from typing import Optional

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/v1/auth/login')

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_access_token(token)
        user_id = int(payload.get('sub'))
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid authentication credentials')
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User not found')
    return user

async def get_current_user_ws(token: Optional[str]) -> Optional[dict]:
    """Get current user for WebSocket connections"""
    if not token:
        return None
    
    try:
        payload = decode_access_token(token)
        user_id = int(payload.get('sub'))
        
        # Get database session
        from app.db.session import AsyncSessionLocal
        db = AsyncSessionLocal()
        try:
            user = await get_user_by_id(db, user_id)
            return user
        finally:
            await db.close()
    except (JWTError, ValueError, TypeError, Exception):
        return None
