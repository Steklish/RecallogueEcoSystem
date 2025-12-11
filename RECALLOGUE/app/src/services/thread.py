from typing import List, Optional
from sqlalchemy.orm import Session
from app.src.models import Thread as ThreadModel
from app.src.repositories import thread_repo
from app.src.schema import Thread, ThreadCreate, ThreadUpdate
from .chat_message import chat_message_service
from fastapi import HTTPException, status

class ThreadService:
    """
    A full-featured service layer for managing threads with proper
    Pydantic schema integration and complete CRUD operations.
    """

    def create(self, db: Session, thread_in: ThreadCreate) -> Thread:
        """
        Creates a new thread.
        - Input: ThreadCreate schema
        - Output: Thread schema (without messages)
        """
        # Create the SQLAlchemy model instance from the Pydantic schema
        db_thread = ThreadModel(
            name=thread_in.name,
            user_id=thread_in.user_id,
            allowed_sources=thread_in.allowed_sources
            # The database will handle defaults for created_at, updated_at
        )

        db.add(db_thread)
        db.commit()
        db.refresh(db_thread)

        # Automatically convert the SQLAlchemy model to a Pydantic schema
        return Thread.from_orm(db_thread)

    def get_by_id(self, db: Session, thread_id: int, include_messages: bool = False) -> Optional[Thread]:
        """
        Retrieves a single thread by its primary key ID.
        Optionally includes all associated messages.
        """
        db_thread = thread_repo.get(db, id=thread_id)
        if not db_thread:
            return None

        # Convert the ORM object to a Pydantic model
        thread = Thread.from_orm(db_thread)

        # If requested, fetch and attach the messages
        if include_messages:
            # Get messages for this thread
            messages = chat_message_service.get_messages_by_thread(db, thread_id=db_thread.id)
            # Add messages as an attribute to the thread object
            thread.messages = messages

        return thread

    def verify_thread_ownership(self, db: Session, thread_id: int, user_id: int) -> bool:
        """
        Verifies if a thread exists and belongs to a specific user.
        Returns True if the thread exists and belongs to the user, False otherwise.
        """
        db_thread = thread_repo.get(db, id=thread_id)
        if not db_thread:
            return False

        return db_thread.user_id == user_id

    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[Thread]:
        """
        Retrieves a list of threads. Messages are not included for performance.
        """
        db_threads = thread_repo.get_multi(db, skip=skip, limit=limit)

        # Use a list comprehension for clean and efficient mapping
        return [Thread.from_orm(thread) for thread in db_threads]

    def get_by_user_id(self, db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Thread]:
        """
        Retrieves a list of threads by user ID. Messages are not included for performance.
        """
        db_threads = thread_repo.get_by_user_id(db, user_id=user_id, skip=skip, limit=limit)

        # Use a list comprehension for clean and efficient mapping
        return [Thread.from_orm(thread) for thread in db_threads]

    def update(self, db: Session, thread_id: int, thread_in: ThreadUpdate) -> Optional[Thread]:
        """
        Updates an existing thread.
        - Input: ThreadUpdate schema with optional fields
        - Output: The updated Thread schema
        """
        db_thread = thread_repo.get(db, id=thread_id)
        if not db_thread:
            return None

        # Get the update data from the Pydantic model
        update_data = thread_in.model_dump(exclude_unset=True)

        # Update the SQLAlchemy model's attributes
        for field, value in update_data.items():
            setattr(db_thread, field, value)

        db.add(db_thread)
        db.commit()
        db.refresh(db_thread)

        return Thread.from_orm(db_thread)

    def delete(self, db: Session, thread_id: int) -> Thread:
        """
        Deletes a thread by its ID.
        Raises an exception if the thread doesn't exist.
        """
        db_thread = thread_repo.get(db, id=thread_id)
        if not db_thread:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")

        # Before returning, convert it to a Pydantic model to send back
        # This is useful to confirm what was deleted
        deleted_thread_data = Thread.from_orm(db_thread)

        db.delete(db_thread)
        db.commit()

        return deleted_thread_data

# A single instance to be used across the application
thread_service = ThreadService()