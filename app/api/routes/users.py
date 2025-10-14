from fastapi import APIRouter, Depends
from app.api.deps import get_current_user

router = APIRouter()

@router.get('/me')
async def read_current_user(current_user = Depends(get_current_user)):
    return current_user
