import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.src.database.base import Base
from app.src.services.user import user_service, access_group_service
from app.src.schema import UserCreate, AccessGroupCreate


# Setup in-memory database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

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


def test_create_access_group(db_session):
    # Test creating an access group
    access_group_in = AccessGroupCreate(name="Admin")
    created_group = access_group_service.create_access_group(db_session, access_group_in)
    
    assert created_group.name == "Admin"
    assert created_group.id is not None


def test_create_user(db_session):
    # First create an access group
    access_group_in = AccessGroupCreate(name="User")
    created_group = access_group_service.create_access_group(db_session, access_group_in)
    
    # Then create a user with that group
    user_in = UserCreate(username="testuser", password="testpassword", group_id=created_group.id)
    created_user = user_service.create_user(db_session, user_in)
    
    assert created_user.username == "testuser"
    assert created_user.group_id == created_group.id
    assert created_user.id is not None


def test_get_user_by_username(db_session):
    # Create an access group first
    access_group_in = AccessGroupCreate(name="Moderator")
    created_group = access_group_service.create_access_group(db_session, access_group_in)
    
    # Create a user
    user_in = UserCreate(username="testuser2", password="testpassword2", group_id=created_group.id)
    user_service.create_user(db_session, user_in)
    
    # Retrieve the user by username
    retrieved_user = user_service.get_user_by_username(db_session, "testuser2")
    
    assert retrieved_user is not None
    assert retrieved_user.username == "testuser2"
    assert retrieved_user.group_id == created_group.id