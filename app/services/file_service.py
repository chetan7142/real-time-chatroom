from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid
import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile
from app.models.file import File
from app.schemas.file import FileUploadResponse
from app.core.config import settings
from app.core.exceptions import FileNotFoundError, UnauthorizedError

# Initialize S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', ''),
    aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', ''),
    region_name=getattr(settings, 'AWS_REGION', 'us-east-1')
)

async def upload_file(db: AsyncSession, file: UploadFile, uploader_id: int) -> FileUploadResponse:
    """Upload a file and return presigned URL for S3 upload"""
    # Generate unique filename
    file_extension = file.filename.split('.')[-1] if '.' in file.filename else ''
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    
    # Create file record in database
    file_record = File(
        uploader_id=uploader_id,
        file_url=f"s3://{settings.S3_BUCKET_NAME}/{unique_filename}",
        file_name=file.filename,
        file_type=file.content_type or 'application/octet-stream',
        file_size=0  # Will be updated after upload
    )
    db.add(file_record)
    await db.flush()  # Get the file ID
    
    # Generate presigned URL for S3 upload
    try:
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': settings.S3_BUCKET_NAME,
                'Key': unique_filename,
                'ContentType': file.content_type
            },
            ExpiresIn=3600  # 1 hour
        )
        
        return FileUploadResponse(
            file_id=file_record.id,
            upload_url=presigned_url,
            expires_in=3600
        )
    except ClientError as e:
        # If S3 fails, delete the database record
        await db.delete(file_record)
        await db.commit()
        raise Exception(f"Failed to generate upload URL: {str(e)}")

async def confirm_file_upload(db: AsyncSession, file_id: int, file_size: int) -> File:
    """Confirm file upload and update file size"""
    result = await db.execute(select(File).where(File.id == file_id))
    file_record = result.scalar_one_or_none()
    
    if not file_record:
        raise FileNotFoundError("File not found")
    
    file_record.file_size = file_size
    await db.commit()
    await db.refresh(file_record)
    return file_record

async def get_user_files(db: AsyncSession, user_id: int) -> List[File]:
    """Get all files uploaded by a user"""
    result = await db.execute(
        select(File).where(File.uploader_id == user_id)
    )
    return result.scalars().all()

async def get_file(db: AsyncSession, file_id: int) -> File:
    """Get a specific file by ID"""
    result = await db.execute(select(File).where(File.id == file_id))
    file_record = result.scalar_one_or_none()
    
    if not file_record:
        raise FileNotFoundError("File not found")
    
    return file_record

async def delete_file(db: AsyncSession, file_id: int, user_id: int) -> bool:
    """Delete a file (only by uploader)"""
    file_record = await get_file(db, file_id)
    
    if file_record.uploader_id != user_id:
        raise UnauthorizedError("You can only delete your own files")
    
    # Delete from S3
    try:
        s3_key = file_record.file_url.split('/')[-1]  # Extract key from S3 URL
        s3_client.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=s3_key)
    except ClientError:
        # Continue even if S3 deletion fails
        pass
    
    # Delete from database
    await db.delete(file_record)
    await db.commit()
    return True

async def get_download_url(db: AsyncSession, file_id: int) -> str:
    """Get presigned URL for file download"""
    file_record = await get_file(db, file_id)
    
    try:
        s3_key = file_record.file_url.split('/')[-1]
        download_url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': settings.S3_BUCKET_NAME,
                'Key': s3_key
            },
            ExpiresIn=3600  # 1 hour
        )
        return download_url
    except ClientError as e:
        raise Exception(f"Failed to generate download URL: {str(e)}")
