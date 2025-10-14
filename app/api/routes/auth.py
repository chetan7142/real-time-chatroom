from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.user import UserCreate, UserRead
from app.db.session import get_db
from app.services.user_service import create_user, authenticate_user, get_user_by_email
from app.core.security import create_access_token

router = APIRouter()

@router.post('/signup', response_model=UserRead, status_code=201)
async def signup(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await get_user_by_email(db, user_in.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Email already registered')
    user = await create_user(db, user_in.username, user_in.email, user_in.password)
    return user

@router.post('/login')
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    # OAuth2PasswordRequestForm gives 'username' and 'password' fields; we use username as email here
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Incorrect email or password')
    access_token = create_access_token(subject=str(user.id))
    return {'access_token': access_token, 'token_type': 'bearer'}
