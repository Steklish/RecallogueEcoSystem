from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.src.models import ChatMessage
from app.src.schema import ChatMessage as ChatMessageSchema, ChatMessageUpdate
from app.src.repositories.base import BaseRepository


class ChatMessageRepository(BaseRepository[ChatMessage, ChatMessageSchema, ChatMessageUpdate]):
    def get_messages_by_thread(self, db: Session, thread_id: int, 
                              skip: int = 0, limit: int = 100) -> List[ChatMessage]:
        return db.query(ChatMessage).filter(
            ChatMessage.thread_id == thread_id
        ).order_by(ChatMessage.timestamp.asc()).offset(skip).limit(limit).all()

    def get_messages_by_role(self, db: Session, thread_id: int, 
                            role: str, skip: int = 0, limit: int = 100) -> List[ChatMessage]:
        return db.query(ChatMessage).filter(
            and_(
                ChatMessage.thread_id == thread_id,
                ChatMessage.role == role
            )
        ).order_by(ChatMessage.timestamp.asc()).offset(skip).limit(limit).all()

    def get_messages_by_time_range(self, db: Session, thread_id: int, 
                                  start_time: datetime, end_time: datetime) -> List[ChatMessage]:
        return db.query(ChatMessage).filter(
            and_(
                ChatMessage.thread_id == thread_id,
                ChatMessage.timestamp >= start_time,
                ChatMessage.timestamp <= end_time
            )
        ).order_by(ChatMessage.timestamp.asc()).all()

    def get_messages_with_filters(self, db: Session, thread_id: int,
                                 role: Optional[str] = None,
                                 search_content: Optional[str] = None,
                                 skip: int = 0, limit: int = 100) -> List[ChatMessage]:
        query = db.query(ChatMessage).filter(ChatMessage.thread_id == thread_id)
        
        if role:
            query = query.filter(ChatMessage.role == role)
        
        if search_content:
            query = query.filter(ChatMessage.content.contains(search_content))
        
        return query.order_by(ChatMessage.timestamp.asc()).offset(skip).limit(limit).all()

    def get_thread_messages_count(self, db: Session, thread_id: int) -> int:
        return db.query(ChatMessage).filter(ChatMessage.thread_id == thread_id).count()


# Create repository instances
chat_message_repo = ChatMessageRepository(ChatMessage)