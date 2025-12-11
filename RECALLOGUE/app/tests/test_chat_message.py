import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.src.database.base import Base
# Import all models to ensure they're registered with Base.metadata
from app.src.models.thread import Thread
from app.src.models.chat_message import ChatMessage
from app.src.models.user import User, AccessGroup
from app.src.services.chat_message import chat_message_service
from app.src.services.thread import thread_service
from app.src.schema import ThreadCreate, ChatMessageCreate, ChatMessageUpdate
from app.src.schema.chat_message import MessageRole


# Setup in-memory database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture
def db_session():
    """Create a new database session with a rollback at the end of each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    # Create tables
    Base.metadata.create_all(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


def test_create_message(db_session):
    # First create a thread
    thread_in = ThreadCreate(name="Test Thread for Messages")
    created_thread = thread_service.create(db_session, thread_in)

    # Test creating a message
    message_in = ChatMessageCreate(
        thread_id=created_thread.id,  # thread_id is required in ChatMessageCreate
        role=MessageRole.USER,
        content="Hello, this is a test message",
        sources=[],
        links=[],
        message_metadata={}
    )
    created_message = chat_message_service.create_message(db_session, created_thread.id, message_in)

    assert created_message.content == "Hello, this is a test message"
    assert created_message.role == MessageRole.USER
    assert created_message.id is not None
    assert created_message.thread_id == created_thread.id


def test_get_message(db_session):
    # First create a thread
    thread_in = ThreadCreate(name="Test Thread for Message Retrieval")
    created_thread = thread_service.create(db_session, thread_in)

    # Create a message
    message_in = ChatMessageCreate(
        thread_id=created_thread.id,
        role=MessageRole.ASSISTANT,
        content="Agent response",
        sources=[],
        links=[],
        message_metadata={}
    )
    created_message = chat_message_service.create_message(db_session, created_thread.id, message_in)

    # Retrieve the message by ID
    retrieved_message = chat_message_service.get_message(db_session, message_id=created_message.id)

    assert retrieved_message is not None
    assert retrieved_message.content == "Agent response"
    assert retrieved_message.id == created_message.id


def test_get_messages_by_thread(db_session):
    # First create a thread
    thread_in = ThreadCreate(name="Test Thread for Multiple Messages")
    created_thread = thread_service.create(db_session, thread_in)

    # Create multiple messages in the same thread
    message_in1 = ChatMessageCreate(
        thread_id=created_thread.id,
        role=MessageRole.USER,
        content="User message 1",
        sources=[],
        links=[],
        message_metadata={}
    )
    message_in2 = ChatMessageCreate(
        thread_id=created_thread.id,
        role=MessageRole.ASSISTANT,
        content="Agent message 1",
        sources=[],
        links=[],
        message_metadata={}
    )
    
    created_message1 = chat_message_service.create_message(db_session, created_thread.id, message_in1)
    created_message2 = chat_message_service.create_message(db_session, created_thread.id, message_in2)

    # Get all messages for the thread
    messages = chat_message_service.get_messages_by_thread(db_session, created_thread.id)

    assert len(messages) >= 2
    message_contents = [m.content for m in messages]
    assert "User message 1" in message_contents
    assert "Agent message 1" in message_contents


def test_get_messages_by_role(db_session):
    # First create a thread
    thread_in = ThreadCreate(name="Test Thread for Role Filtering")
    created_thread = thread_service.create(db_session, thread_in)

    # Create messages with different roles
    user_message_in = ChatMessageCreate(
        thread_id=created_thread.id,
        role=MessageRole.USER,
        content="User message",
        sources=[],
        links=[],
        message_metadata={}
    )
    agent_message_in = ChatMessageCreate(
        thread_id=created_thread.id,
        role=MessageRole.ASSISTANT,
        content="Agent message",
        sources=[],
        links=[],
        message_metadata={}
    )
    
    chat_message_service.create_message(db_session, created_thread.id, user_message_in)
    chat_message_service.create_message(db_session, created_thread.id, agent_message_in)

    # Filter messages by role
    user_messages = chat_message_service.get_messages_by_role(db_session, created_thread.id, "user")
    agent_messages = chat_message_service.get_messages_by_role(db_session, created_thread.id, "assistant")  # assuming agent maps to assistant

    assert len(user_messages) >= 1
    assert len(agent_messages) >= 1


def test_delete_message(db_session):
    # First create a thread
    thread_in = ThreadCreate(name="Test Thread for Message Deletion")
    created_thread = thread_service.create(db_session, thread_in)

    # Create a message
    message_in = ChatMessageCreate(
        thread_id=created_thread.id,
        role=MessageRole.USER,
        content="Message to delete",
        sources=[],
        links=[],
        message_metadata={}
    )
    created_message = chat_message_service.create_message(db_session, created_thread.id, message_in)

    # Delete the message
    result = chat_message_service.delete_message(db_session, message_id=created_message.id)

    assert result is True

    # Verify the message was deleted by trying to retrieve it
    retrieved_message = chat_message_service.get_message(db_session, message_id=created_message.id)
    assert retrieved_message is None