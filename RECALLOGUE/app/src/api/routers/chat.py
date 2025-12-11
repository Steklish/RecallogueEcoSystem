import json
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

# --- Local Imports ---
# Assumes a standard project structure
from app.src.database.session import get_db
from app.src.auth.dependencies import get_current_user_from_cookie
from app.src.schema.message_schemas import UserMessageRequest
from app.src.services import chat_service
from app.src.services.chat_message import chat_message_service
from app.src.services.thread import thread_service
from app.src.schema import ChatMessage, ChatMessageCreate, ChatMessageUpdate
from app.src.models import User as UserModel, Thread as ThreadModel

# ==============================================================================
# Router Definition
# ==============================================================================


router = APIRouter(
    prefix="/chat",
    tags=["Chat Messages"],
    dependencies=[Depends(get_current_user_from_cookie)]
)

# ==============================================================================
# Endpoint Definitions
# ==============================================================================

@router.post("/{thread_id}/chat")
async def chat_in_thread(message: UserMessageRequest, user : UserModel = Depends(get_current_user_from_cookie)):
    try:
        def stream_generator():
            for chunk in chat_service.message_request(message):
                yield f"data: {json.dumps({'type': 'chunk', 'data': chunk}, ensure_ascii=False)}\n\n"
        
        return StreamingResponse(stream_generator(), media_type="text/event-stream")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/messages", response_model=ChatMessage, status_code=status.HTTP_201_CREATED)
def create_new_message(
    message_in: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user_from_cookie)
):
    """
    Create a new chat message in a thread.
    """
    # First, verify the thread exists and belongs to the current user
    thread = thread_service.get_by_id(db, thread_id=message_in.thread_id)
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )

    if thread.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to add messages to this thread."
        )

    # Create the message
    return chat_message_service.create_message(db=db, thread_id=message_in.thread_id, message=message_in)


@router.get("/messages/{message_id}", response_model=ChatMessage)
def get_single_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user_from_cookie)
):
    """
    Retrieve a specific message by its ID.
    A user can only retrieve a message from a thread that they own.
    """
    message = chat_message_service.get_message(db, message_id=message_id)

    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")

    # Check thread ownership using thread service
    if not thread_service.verify_thread_ownership(db, thread_id=message.thread_id, user_id=current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this message")

    return message


@router.get("/threads/{thread_id}/messages", response_model=List[ChatMessage])
def get_messages_by_thread(
    thread_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user_from_cookie),
    skip: int = 0,
    limit: int = 100
):
    """
    Retrieve all messages for a specific thread.
    A user can only retrieve messages from threads that they own.
    """
    # First verify the thread exists and is owned by the user
    if not thread_service.verify_thread_ownership(db, thread_id=thread_id, user_id=current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")

    # Get messages from the thread
    return chat_message_service.get_messages_by_thread(db, thread_id=thread_id, skip=skip, limit=limit)


@router.get("/threads/{thread_id}/messages/role/{role}", response_model=List[ChatMessage])
def get_messages_by_thread_and_role(
    thread_id: int,
    role: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user_from_cookie),
    skip: int = 0,
    limit: int = 100
):
    """
    Retrieve messages filtered by role within a specific thread.
    A user can only retrieve messages from threads that they own.
    """
    # First verify the thread exists and is owned by the user
    if not thread_service.verify_thread_ownership(db, thread_id=thread_id, user_id=current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")

    # Get messages with the specified role from the thread
    return chat_message_service.get_messages_by_role(db, thread_id=thread_id, role=role, skip=skip, limit=limit)


@router.get("/threads/{thread_id}/messages/search", response_model=List[ChatMessage])
def get_messages_with_filters(
    thread_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user_from_cookie),
    role: str | None = None,
    search_content: str | None = None,
    skip: int = 0,
    limit: int = 100
):
    """
    Retrieve messages with optional filters for role and content within a specific thread.
    A user can only retrieve messages from threads that they own.
    """
    # First verify the thread exists and is owned by the user
    if not thread_service.verify_thread_ownership(db, thread_id=thread_id, user_id=current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")

    # Get messages with filters
    return chat_message_service.get_messages_with_filters(
        db,
        thread_id=thread_id,
        role=role,
        search_content=search_content,
        skip=skip,
        limit=limit
    )


@router.get("/threads/{thread_id}/messages/time_range", response_model=List[ChatMessage])
def get_messages_by_time_range(
    thread_id: int,
    start_time: datetime,
    end_time: datetime,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user_from_cookie)
):
    """
    Retrieve messages within a specific time range for a thread.
    A user can only retrieve messages from threads that they own.
    """
    # First verify the thread exists and is owned by the user
    if not thread_service.verify_thread_ownership(db, thread_id=thread_id, user_id=current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")

    # Get messages within the time range
    return chat_message_service.get_messages_by_time_range(
        db,
        thread_id=thread_id,
        start_time=start_time,
        end_time=end_time
    )


@router.put("/messages/{message_id}", response_model=ChatMessage)
def update_existing_message(
    message_id: int,
    message_in: ChatMessageUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user_from_cookie)
):
    """
    Update the properties of an existing message (e.g., its content).
    A user can only update a message from a thread that they own.
    """
    # First, get the message to check if it exists
    existing_message = chat_message_service.get_message(db, message_id=message_id)
    if not existing_message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")

    # Check thread ownership using thread service
    if not thread_service.verify_thread_ownership(db, thread_id=existing_message.thread_id, user_id=current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this message")

    # Update the message
    updated_message = chat_message_service.update_message(db, message_id=message_id, message_update=message_in)
    if not updated_message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found after update attempt")

    return updated_message


@router.delete("/messages/{message_id}", response_model=ChatMessage)
def delete_message_by_id(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user_from_cookie)
):
    """
    Permanently delete a message.
    A user can only delete a message from a thread that they own.
    Returns the data of the deleted message as confirmation.
    """
    # First, get the message to check if it exists
    existing_message = chat_message_service.get_message(db, message_id=message_id)
    if not existing_message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")

    # Check thread ownership using thread service
    if not thread_service.verify_thread_ownership(db, thread_id=existing_message.thread_id, user_id=current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this message")

    # Delete the message
    success = chat_message_service.delete_message(db, message_id=message_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")

    return existing_message