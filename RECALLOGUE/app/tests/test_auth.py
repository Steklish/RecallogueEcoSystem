import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.src.database.base import Base
# Import all models to ensure they're registered with Base.metadata
from app.src.models.user import User, AccessGroup
from app.src.services.auth import auth_service
from app.src.services.user import user_service
from app.src.schema import UserCreate
from fastapi.security import OAuth2PasswordRequestForm


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


def test_authenticate_user_success(db_session):
    # First create a user
    user_in = UserCreate(username="testuser", password="testpassword", group_id=None)
    created_user = user_service.create_user(db_session, user_in)

    # Authenticate the user with correct credentials
    authenticated_user = auth_service.authenticate_user(
        db_session, username="testuser", password="testpassword"
    )

    assert authenticated_user is not None
    assert authenticated_user.username == "testuser"


def test_authenticate_user_invalid_username(db_session):
    # Try to authenticate with non-existent user
    authenticated_user = auth_service.authenticate_user(
        db_session, username="nonexistent", password="password"
    )

    assert authenticated_user is None


def test_authenticate_user_invalid_password(db_session):
    # First create a user
    user_in = UserCreate(username="testuser2", password="testpassword2", group_id=None)
    created_user = user_service.create_user(db_session, user_in)

    # Try to authenticate with wrong password
    authenticated_user = auth_service.authenticate_user(
        db_session, username="testuser2", password="wrongpassword"
    )

    assert authenticated_user is None


def test_login_and_create_token_success(db_session):
    # First create a user
    user_in = UserCreate(username="testuser3", password="testpassword3", group_id=None)
    created_user = user_service.create_user(db_session, user_in)

    # Create form data for login
    form_data = OAuth2PasswordRequestForm(username="testuser3", password="testpassword3", scope="")

    # Login and create token
    token = auth_service.login_and_create_token(db_session, form_data)

    assert token is not None
    assert token.access_token is not None
    assert token.token_type == "bearer"


def test_login_and_create_token_invalid_credentials(db_session):
    # Create form data for login with invalid credentials
    form_data = OAuth2PasswordRequestForm(username="testuser4", password="wrongpassword", scope="")

    # Try to login with non-existent user - should raise an exception
    with pytest.raises(Exception):
        auth_service.login_and_create_token(db_session, form_data)