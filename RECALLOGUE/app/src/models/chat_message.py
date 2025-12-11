from sqlalchemy import Integer, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.src.database.base import Base
from app.src.models.thread import Thread


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    thread_id: Mapped[int] = mapped_column(Integer, ForeignKey("threads.id"), nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)  # user, assistant, system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    sources: Mapped[list | None] = mapped_column(JSON)  # Store as JSON array
    links: Mapped[list | None] = mapped_column(JSON)  # Store as JSON array
    message_metadata: Mapped[dict | None] = mapped_column(JSON)  # Store as JSON object (renamed from 'metadata' to avoid SQLAlchemy conflict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)