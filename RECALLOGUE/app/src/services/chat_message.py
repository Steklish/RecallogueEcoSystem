from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
# It's good practice to import and alias to avoid confusion
from app.src.models import ChatMessage as ChatMessageModel
from app.src.models import Thread as ThreadModel
from app.src.repositories import thread_repo, chat_message_repo
# Import all the schemas you defined
from app.src.schema import (
    ChatMessage,
    ChatMessageCreate,
    ChatMessageUpdate
)
# For better API error handling, use HTTPException
from fastapi import HTTPException, status

class ChatMessageService:
    """
    A service layer that leverages Pydantic for clean data contracts and mapping.
    """
    def create_message(self, db: Session, thread_id: int, message: ChatMessageCreate) -> ChatMessage:
        """
        Creates a new message in a thread.
        - Input: ChatMessageCreate schema
        - Output: ChatMessage schema
        """
        # First, get the thread to ensure it exists
        db_thread = thread_repo.get(db, id=thread_id)
        if not db_thread:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Thread with ID {thread_id} not found",
            )

        # Create the SQLAlchemy model instance from the Pydantic create model
        db_message = ChatMessageModel(
            thread_id=db_thread.id,
            role=message.role.value,  # Use .value to get the string from the Enum
            content=message.content,
            sources=message.sources,
            links=message.links,
            message_metadata=message.message_metadata  # Pydantic handles the alias on input
        )

        # The database will handle defaults for timestamp and created_at
        db.add(db_message)
        db.commit()
        db.refresh(db_message)

        # Automatically convert the SQLAlchemy model to a Pydantic schema for the response
        return ChatMessage.from_orm(db_message)

    def get_message(self, db: Session, message_id: int) -> Optional[ChatMessage]:
        """
        Retrieves a single message by its ID.
        """
        db_message = chat_message_repo.get(db, id=message_id)
        if db_message:
            return ChatMessage.from_orm(db_message)
        return None

    def get_messages_by_thread(self, db: Session, thread_id: int,
                              skip: int = 0, limit: int = 100) -> List[ChatMessage]:
        """
        Retrieves all messages for a given thread using automatic schema mapping.
        """
        db_thread = thread_repo.get(db, id=thread_id)
        if not db_thread:
            return []

        db_messages = chat_message_repo.get_messages_by_thread(db, db_thread.id, skip, limit)

        # Use a list comprehension for a clean and efficient mapping
        return [ChatMessage.from_orm(msg) for msg in db_messages]

    def get_messages_by_role(self, db: Session, thread_id: int, role: str,
                            skip: int = 0, limit: int = 100) -> List[ChatMessage]:
        """
        Retrieves messages filtered by role within a thread.
        """
        db_thread = thread_repo.get(db, id=thread_id)
        if not db_thread:
            return []

        db_messages = chat_message_repo.get_messages_by_role(db, db_thread.id, role, skip, limit)
        return [ChatMessage.from_orm(msg) for msg in db_messages]

    def get_messages_by_time_range(self, db: Session, thread_id: int,
                                  start_time: datetime, end_time: datetime) -> List[ChatMessage]:
        """
        Retrieves messages within a specific time range for a thread.
        """
        db_thread = thread_repo.get(db, id=thread_id)
        if not db_thread:
            return []

        db_messages = chat_message_repo.get_messages_by_time_range(db, db_thread.id, start_time, end_time)
        return [ChatMessage.from_orm(msg) for msg in db_messages]

    def get_messages_with_filters(self, db: Session, thread_id: int,
                                 role: Optional[str] = None,
                                 search_content: Optional[str] = None,
                                 skip: int = 0, limit: int = 100) -> List[ChatMessage]:
        """
        Retrieves messages with optional filters for role and content.
        """
        db_thread = thread_repo.get(db, id=thread_id)
        if not db_thread:
            return []

        db_messages = chat_message_repo.get_messages_with_filters(
            db, db_thread.id, role, search_content, skip, limit
        )
        return [ChatMessage.from_orm(msg) for msg in db_messages]

    def update_message(self, db: Session, message_id: int, message_update: ChatMessageUpdate) -> Optional[ChatMessage]:
        """
        Updates an existing message.
        """
        db_message = chat_message_repo.get(db, id=message_id)
        if not db_message:
            return None

        # Update the message fields based on the update schema
        update_data = message_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(db_message, field):
                setattr(db_message, field, value)

        db.commit()
        db.refresh(db_message)

        return ChatMessage.from_orm(db_message)

    def delete_message(self, db: Session, message_id: int) -> bool:
        """
        Deletes a message by its ID.
        """
        # This logic remains the same as it doesn't involve schema conversion
        db_message = chat_message_repo.get(db, id=message_id)
        if not db_message:
            return False

        db.delete(db_message)
        db.commit()
        return True


# Create a single service instance to be used throughout the application
chat_message_service = ChatMessageService()