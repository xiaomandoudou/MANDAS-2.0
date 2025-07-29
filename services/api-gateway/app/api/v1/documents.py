from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List
import uuid
import os
import aiofiles
from datetime import datetime

from app.core.database import get_db, KnowledgeBaseDocs
from app.core.config import settings
from app.core.auth import get_current_user
from loguru import logger

router = APIRouter()


class DocumentResponse(BaseModel):
    id: str
    file_name: str
    file_size: int
    mime_type: str
    status: str
    created_at: datetime


@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if file.size > settings.max_file_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {settings.max_file_size} bytes"
        )
    
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in settings.allowed_file_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file_extension} not allowed. Allowed types: {settings.allowed_file_types}"
        )
    
    doc_id = uuid.uuid4()
    upload_dir = f"/app/uploads/{current_user['sub']}"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = f"{upload_dir}/{doc_id}_{file.filename}"
    
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        new_doc = KnowledgeBaseDocs(
            id=doc_id,
            user_id=uuid.UUID(current_user["sub"]),
            file_name=file.filename,
            file_path=file_path,
            file_size=file.size,
            mime_type=file.content_type,
            status="PROCESSING"
        )
        
        db.add(new_doc)
        await db.commit()
        await db.refresh(new_doc)
        
        logger.info(f"Document {doc_id} uploaded successfully for user {current_user['username']}")
        
        return {
            "document_id": str(doc_id),
            "status": "PROCESSING",
            "message": "文档上传成功，正在处理中。",
            "file_name": file.filename
        }
        
    except Exception as e:
        logger.error(f"Failed to upload document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document"
        )


@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(KnowledgeBaseDocs).where(
            KnowledgeBaseDocs.user_id == uuid.UUID(current_user["sub"])
        ).order_by(KnowledgeBaseDocs.created_at.desc())
    )
    documents = result.scalars().all()
    
    return [
        {
            "id": str(doc.id),
            "file_name": doc.file_name,
            "file_size": doc.file_size,
            "mime_type": doc.mime_type,
            "status": doc.status,
            "created_at": doc.created_at
        }
        for doc in documents
    ]


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID format"
        )
    
    result = await db.execute(
        select(KnowledgeBaseDocs).where(
            KnowledgeBaseDocs.id == doc_uuid,
            KnowledgeBaseDocs.user_id == uuid.UUID(current_user["sub"])
        )
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    try:
        if document.file_path and os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        await db.delete(document)
        await db.commit()
        
        logger.info(f"Document {document_id} deleted successfully")
        
        return {"message": "Document deleted successfully"}
        
    except Exception as e:
        logger.error(f"Failed to delete document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document"
        )
