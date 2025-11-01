from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.schemas.file import FileRead, FileUploadResponse
from app.schemas.user import UserRead
from app.db.session import get_db
from app.api.deps import get_current_user
from app.services.file_service import upload_file, get_user_files, delete_file
from app.core.exceptions import FileNotFoundError, UnauthorizedError

router = APIRouter()

@router.post('/upload', response_model=FileUploadResponse, status_code=201)
async def upload_file_endpoint(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(get_current_user)
):
    """Upload a file and get presigned URL for S3"""
    try:
        result = await upload_file(db, file, current_user.id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get('/', response_model=List[FileRead])
async def get_user_files_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(get_current_user)
):
    """Get all files uploaded by the current user"""
    files = await get_user_files(db, current_user.id)
    return files

@router.delete('/{file_id}')
async def delete_file_endpoint(
    file_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(get_current_user)
):
    """Delete a file"""
    try:
        await delete_file(db, file_id, current_user.id)
        return {"message": "File deleted successfully"}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except UnauthorizedError:
        raise HTTPException(status_code=403, detail="You can only delete your own files")
