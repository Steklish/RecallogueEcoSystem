from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

# --- Local Imports ---
# Assumes a standard project structure
from app.src.database.session import get_db
from app.src.auth.dependencies import get_current_user_from_cookie
from app.src.services.thread import thread_service
from app.src.schema import Thread, ThreadCreate, ThreadUpdate
from app.src.models import User as UserModel

# ==============================================================================
# Router Definition
# ==============================================================================


router = APIRouter(
    prefix="/threads",
    tags=["Threads"],
    dependencies=[Depends(get_current_user_from_cookie)]
)

# ==============================================================================
# Endpoint Definitions
# ==============================================================================

@router.post("/", response_model=Thread, status_code=status.HTTP_201_CREATED)
def create_new_thread(
    thread_in: ThreadCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user_from_cookie)
):
    """
    Create a new chat thread for the currently authenticated user.
    """
    # Security: Ensure the user_id in the payload matches the authenticated user
    if thread_in.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to create a thread for another user."
        )
    
    # The service layer handles the database logic
    return thread_service.create(db=db, thread_in=thread_in)


@router.get("/", response_model=List[Thread])
def get_user_threads(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user_from_cookie),
    skip: int = 0,
    limit: int = 100
):
    """
    Retrieve all threads owned by the currently authenticated user.
    """
    # Correct implementation requires fetching by user ID
    return thread_service.get_by_user_id(db, user_id=current_user.id, skip=skip, limit=limit) # type: ignore
    

@router.get("/{thread_id}", response_model=Thread)
def get_single_thread(
    thread_id: int,
    include_messages: bool = False,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user_from_cookie)
):
    """
    Retrieve a specific thread by its ID.
    
    - A user can only retrieve a thread that they own.
    - Use the `include_messages` query parameter to optionally embed all
      chat messages associated with this thread.
    """
    thread = thread_service.get_by_id(db, thread_id=thread_id, include_messages=include_messages)

    if not thread:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")

    # Security: Ensure the user owns the thread they are trying to access
    if thread.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this thread")
        
    return thread


@router.put("/{thread_id}", response_model=Thread)
def update_existing_thread(
    thread_id: int,
    thread_in: ThreadUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user_from_cookie)
):
    """
    Update the properties of an existing thread (e.g., its name).
    A user can only update a thread that they own.
    """
    # First, verify the thread exists and the user owns it
    existing_thread = thread_service.get_by_id(db, thread_id=thread_id)
    if not existing_thread:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")
    
    if existing_thread.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this thread")

    # If checks pass, proceed with the update
    updated_thread = thread_service.update(db, thread_id=thread_id, thread_in=thread_in)
    return updated_thread


@router.delete("/{thread_id}", response_model=Thread)
def delete_thread_by_id(
    thread_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user_from_cookie)
):
    """

    Permanently delete a thread.
    A user can only delete a thread that they own.
    Returns the data of the deleted thread as confirmation.
    """
    # Verify the thread exists and the user owns it before attempting to delete
    thread_to_delete = thread_service.get_by_id(db, thread_id=thread_id)
    if not thread_to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")
        
    if thread_to_delete.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this thread")

    # The service layer handles the actual deletion and raises a 404 if it's already gone
    deleted_thread = thread_service.delete(db, thread_id=thread_id)
    return deleted_thread