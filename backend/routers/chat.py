"""
Chat Router
Handles chat interactions with the AI agent
"""
import uuid
import os
import base64
import tempfile
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from langchain_core.messages import HumanMessage

from backend.models.chat import (
    ChatRequest, ChatResponse, FileUploadResponse,
    TextChatRequest, PdfChatRequest, ImageChatRequest
)
from backend.dependencies import get_current_user, get_app_container
from chatbot.core.history import save_session_message
from chatbot.core.file_store import save_pdf_to_mongo


router = APIRouter(prefix="/chat", tags=["Chat"])

# Mai làm cái xác thực email người dùng. Mở bên antigravity trước. Hỏi kĩ lại is_active là user đang hoạt động hay ý nghĩa gì
@router.post(
    "/text",
    response_model=ChatResponse,
    summary="Send a text-only chat message",
    description="Send a text message to the AI chatbot (no image support)"
)
async def chat_text(
    request: TextChatRequest,
    current_user: dict = Depends(get_current_user),
    app=Depends(get_app_container)
):
    """
    Chat với AI bằng tin nhắn văn bản.
    
    - **message**: Nội dung tin nhắn
    - **session_id**: ID phiên chat (tạo mới nếu không cung cấp)
    """
    if not app.agent_executor:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI agent is not ready. Please try again later."
        )
    
    user_id = str(current_user["_id"])
    session_id = request.session_id or str(uuid.uuid4())
    
    try:
        user_profile = app.memory_service.get_profile(user_id) if app.memory_service else None
        
        inputs = {
            "messages": [HumanMessage(content=request.message)],
            "user_info": user_profile or "Chưa có thông tin.",
            "image_path": None  # No image for text chat
        }
        
        result = app.agent_executor.invoke(
            inputs,
            config={"configurable": {"session_id": session_id, "user_id": user_id}}
        )
        
        last_message = result["messages"][-1]
        response_text = last_message.content
        agent_name = getattr(last_message, 'name', None)
        
        save_session_message(
            session_id=session_id,
            user_id=user_id,
            question=request.message,
            answer=response_text
        )
        
        if app.memory_service:
            app.memory_service.update_profile_background(user_id, request.message)
        
        return ChatResponse(
            session_id=session_id,
            response=response_text,
            agent_name=agent_name
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing message: {str(e)}"
        )


@router.post(
    "/image",
    response_model=ChatResponse,
    summary="Send a chat message with an image",
    description="Upload an image and ask AI to analyze it"
)
async def chat_image(
    message: str = Form(..., min_length=1, max_length=10000, description="Câu hỏi về ảnh"),
    image: UploadFile = File(..., description="File ảnh (jpg, png, gif, webp)"),
    session_id: Optional[str] = Form(None, description="ID phiên chat"),
    current_user: dict = Depends(get_current_user),
    app = Depends(get_app_container)
):
    """
    Chat với AI kèm hình ảnh để phân tích.
    
    - **message**: Câu hỏi về ảnh (ví dụ: "Mô tả ảnh này")
    - **image**: File ảnh upload trực tiếp (jpg, png, gif, webp)
    - **session_id**: ID phiên chat (tạo mới nếu không cung cấp)
    """
    if not app.agent_executor:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI agent is not ready. Please try again later."
        )
    
    # Validate image type
    allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    if image.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Chỉ hỗ trợ các định dạng ảnh: jpg, png, gif, webp. Đã nhận: {image.content_type}"
        )
    
    user_id = str(current_user["_id"])
    session_id = session_id or str(uuid.uuid4())
    
    # Save uploaded image temporarily
    image_path = None
    try:
        # Determine file extension
        ext = image.filename.split('.')[-1] if image.filename else 'jpg'
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
            content = await image.read()
            tmp.write(content)
            image_path = tmp.name
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Lỗi đọc file ảnh: {e}"
        )
    
    try:
        user_profile = app.memory_service.get_profile(user_id) if app.memory_service else None
        
        inputs = {
            "messages": [HumanMessage(content=message)],
            "user_info": user_profile or "Chưa có thông tin.",
            "image_path": image_path
        }
        
        result = app.agent_executor.invoke(
            inputs,
            config={"configurable": {"session_id": session_id, "user_id": user_id}}
        )
        
        last_message = result["messages"][-1]
        response_text = last_message.content
        agent_name = getattr(last_message, 'name', None)
        
        save_session_message(
            session_id=session_id,
            user_id=user_id,
            question=message,
            answer=response_text,
            image_gridfs_id=image_path
        )
        
        if app.memory_service:
            app.memory_service.update_profile_background(user_id, message)
        
        return ChatResponse(
            session_id=session_id,
            response=response_text,
            agent_name=agent_name
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing message: {str(e)}"
        )
    finally:
        if image_path and os.path.exists(image_path):
            try:
                os.remove(image_path)
            except:
                pass


@router.post(
    "/pdf",
    response_model=ChatResponse,
    summary="Send a chat message about uploaded PDF",
    description="Send a message to query content from uploaded PDF files"
)
async def chat_pdf(
    request: PdfChatRequest,
    current_user: dict = Depends(get_current_user),
    app = Depends(get_app_container)
):
    """
    Chat với AI về nội dung PDF đã tải lên.
    
    - **message**: Câu hỏi về nội dung PDF
    - **session_id**: ID phiên chat (tạo mới nếu không cung cấp)
    - **file_id**: ID của file PDF đã upload (tùy chọn, nếu không có sẽ tìm trong tất cả file của user)
    """
    if not app.agent_executor:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI agent is not ready. Please try again later."
        )
    
    user_id = str(current_user["_id"])
    session_id = request.session_id or str(uuid.uuid4())
    
    try:
        user_profile = app.memory_service.get_profile(user_id) if app.memory_service else None
        
        # Add hint for PDF context if file_id provided
        message_content = request.message
        if request.file_id:
            message_content = f"[Tìm trong file PDF: {request.file_id}] {request.message}"
        
        inputs = {
            "messages": [HumanMessage(content=message_content)],
            "user_info": user_profile or "Chưa có thông tin.",
            "image_path": None
        }
        
        result = app.agent_executor.invoke(
            inputs,
            config={"configurable": {"session_id": session_id, "user_id": user_id}}
        )
        
        last_message = result["messages"][-1]
        response_text = last_message.content
        agent_name = getattr(last_message, 'name', None)
        
        save_session_message(
            session_id=session_id,
            user_id=user_id,
            question=request.message,
            answer=response_text
        )
        
        if app.memory_service:
            app.memory_service.update_profile_background(user_id, request.message)
        
        return ChatResponse(
            session_id=session_id,
            response=response_text,
            agent_name=agent_name
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing message: {str(e)}"
        )


@router.post(
    "/upload",
    response_model=FileUploadResponse,
    summary="Upload a PDF file",
    description="Upload a PDF file for the chatbot to use in responses"
)
async def upload_file(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload a PDF file for RAG (Retrieval-Augmented Generation).
    
    The file will be processed in the background and become available
    for queries once processing is complete.
    
    - **file**: PDF file to upload
    - **session_id**: Optional session ID to associate the file with
    """
    user_id = str(current_user["_id"])
    session_id = session_id or str(uuid.uuid4())
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported"
        )
    
    # Save file temporarily
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            content = await file.read()
            tmp.write(content)
            temp_path = tmp.name
        
        # Save to MongoDB/GridFS
        file_id = save_pdf_to_mongo(temp_path, session_id, user_id)
        
        if not file_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save file"
            )
        
        return FileUploadResponse(
            file_id=str(file_id),
            filename=file.filename,
            status="processing",
            message="File uploaded successfully. Processing in background."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file: {str(e)}"
        )
    finally:
        # Clean up temp file
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
