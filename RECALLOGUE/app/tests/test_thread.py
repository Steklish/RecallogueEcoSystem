import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.src.database.base import Base
# Import all models to ensure they're registered with Base.metadata
from app.src.models.thread import Thread
from app.src.models.chat_message import ChatMessage
from app.src.models.user import User, AccessGroup
from app.src.services.thread import thread_service
from app.src.schema import ThreadCreate, ThreadUpdate


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


def test_create_thread(db_session):
    # First create a user to associate with the thread
    from app.src.models.user import User
    from app.src.services.user import user_service
    from app.src.schema import UserCreate

    user_in = UserCreate(username="test_user", password="test_password")
    user = user_service.create_user(db_session, user_in)

    # Test creating a thread
    thread_in = ThreadCreate(name="Test Thread", user_id=user.id)
    created_thread = thread_service.create(db_session, thread_in)

    assert created_thread.name == "Test Thread"
    assert created_thread.id is not None
    assert created_thread.user_id == user.id


def test_get_thread_by_id(db_session):
    # First create a user to associate with the thread
    from app.src.services.user import user_service
    from app.src.schema import UserCreate

    user_in = UserCreate(username="test_user2", password="test_password")
    user = user_service.create_user(db_session, user_in)

    # First create a thread
    thread_in = ThreadCreate(name="Test Thread for Retrieval", user_id=user.id)
    created_thread = thread_service.create(db_session, thread_in)

    # Retrieve the thread by ID
    retrieved_thread = thread_service.get_by_id(db_session, thread_id=created_thread.id)

    assert retrieved_thread is not None
    assert retrieved_thread.name == "Test Thread for Retrieval"
    assert retrieved_thread.id == created_thread.id
    assert retrieved_thread.user_id == user.id


def test_get_all_threads(db_session):
    # First create a user to associate with the threads
    from app.src.services.user import user_service
    from app.src.schema import UserCreate

    user_in = UserCreate(username="test_user3", password="test_password")
    user = user_service.create_user(db_session, user_in)

    # Create multiple threads
    thread_in1 = ThreadCreate(name="Thread 1", user_id=user.id)
    thread_in2 = ThreadCreate(name="Thread 2", user_id=user.id)

    created_thread1 = thread_service.create(db_session, thread_in1)
    created_thread2 = thread_service.create(db_session, thread_in2)

    # Get all threads
    threads = thread_service.get_all(db_session)

    assert len(threads) >= 2
    thread_names = [t.name for t in threads]
    assert "Thread 1" in thread_names
    assert "Thread 2" in thread_names


def test_update_thread(db_session):
    # First create a user to associate with the thread
    from app.src.services.user import user_service
    from app.src.schema import UserCreate

    user_in = UserCreate(username="test_user4", password="test_password")
    user = user_service.create_user(db_session, user_in)

    # First create a thread
    thread_in = ThreadCreate(name="Original Thread", user_id=user.id)
    created_thread = thread_service.create(db_session, thread_in)

    # Update the thread
    update_data = ThreadUpdate(name="Updated Thread")
    updated_thread = thread_service.update(db_session, thread_id=created_thread.id, thread_in=update_data)

    assert updated_thread is not None
    assert updated_thread.name == "Updated Thread"


def test_delete_thread(db_session):
    # First create a user to associate with the thread
    from app.src.services.user import user_service
    from app.src.schema import UserCreate

    user_in = UserCreate(username="test_user5", password="test_password")
    user = user_service.create_user(db_session, user_in)

    # First create a thread
    thread_in = ThreadCreate(name="Thread to Delete", user_id=user.id)
    created_thread = thread_service.create(db_session, thread_in)

    # Delete the thread
    deleted_thread = thread_service.delete(db_session, thread_id=created_thread.id)

    assert deleted_thread is not None
    assert deleted_thread.name == "Thread to Delete"

    # Verify the thread was deleted by trying to retrieve it
    retrieved_thread = thread_service.get_by_id(db_session, thread_id=created_thread.id)
    assert retrieved_thread is None


def test_get_threads_by_user_id(db_session):
    # Create two different users
    from app.src.services.user import user_service
    from app.src.schema import UserCreate

    user1_in = UserCreate(username="test_user_thread1", password="test_password")
    user2_in = UserCreate(username="test_user_thread2", password="test_password")
    user1 = user_service.create_user(db_session, user1_in)
    user2 = user_service.create_user(db_session, user2_in)

    # Create threads for user1
    thread1 = ThreadCreate(name="User1 Thread 1", user_id=user1.id)
    thread2 = ThreadCreate(name="User1 Thread 2", user_id=user1.id)
    created_thread1 = thread_service.create(db_session, thread1)
    created_thread2 = thread_service.create(db_session, thread2)

    # Create threads for user2
    thread3 = ThreadCreate(name="User2 Thread 1", user_id=user2.id)
    created_thread3 = thread_service.create(db_session, thread3)

    # Get threads for user1 - should only get user1's threads
    user1_threads = thread_service.get_by_user_id(db_session, user_id=user1.id)
    assert len(user1_threads) == 2
    thread_names = [t.name for t in user1_threads]
    assert "User1 Thread 1" in thread_names
    assert "User1 Thread 2" in thread_names
    for thread in user1_threads:
        assert thread.user_id == user1.id

    # Get threads for user2 - should only get user2's thread
    user2_threads = thread_service.get_by_user_id(db_session, user_id=user2.id)
    assert len(user2_threads) == 1
    assert user2_threads[0].name == "User2 Thread 1"
    assert user2_threads[0].user_id == user2.id

    # Check that user2 doesn't have user1's threads
    user2_thread_names = [t.name for t in user2_threads]
    assert "User1 Thread 1" not in user2_thread_names
    assert "User1 Thread 2" not in user2_thread_names