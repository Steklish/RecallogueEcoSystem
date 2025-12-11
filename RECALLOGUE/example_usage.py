"""
Example usage of the User and Access Group functionality
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.src.database.base import Base
from app.src.services.user import user_service, access_group_service
from app.src.schema import UserCreate, AccessGroupCreate


# Create an in-memory database for the example
# Using a different database to not interfere with the main app
SQLALCHEMY_DATABASE_URL = "sqlite:///./example.db"

# Remove existing database to avoid constraint errors
if os.path.exists("./example.db"):
    os.remove("./example.db")

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


def example_usage():
    # Create a database session
    db = SessionLocal()
    
    try:
        # Create an access group
        admin_group = AccessGroupCreate(name="Administrators")
        created_group = access_group_service.create_access_group(db, admin_group)
        print(f"Created access group: {created_group.name} with ID: {created_group.id}")
        
        # Create a user with the access group
        user_data = UserCreate(
            username="admin_user",
            password="secure_password",
            group_id=created_group.id
        )
        created_user = user_service.create_user(db, user_data)
        print(f"Created user: {created_user.username} with ID: {created_user.id}")
        
        # Retrieve the user by username
        retrieved_user = user_service.get_user_by_username(db, "admin_user")
        if retrieved_user:
            print(f"Retrieved user: {retrieved_user.username}")
            print(f"Group ID: {retrieved_user.group_id}")
        
        # List all access groups
        all_groups = access_group_service.get_access_groups(db)
        print(f"Total access groups: {len(all_groups)}")
        
        # List all users
        all_users = user_service.get_users(db)
        print(f"Total users: {len(all_users)}")
        
    finally:
        db.close()


if __name__ == "__main__":
    example_usage()