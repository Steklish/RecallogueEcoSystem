from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.src.database.base import Base
from app.src.models.thread import Thread
from app.src.models.user import User, AccessGroup
from app.src.models.chat_message import ChatMessage

def test_schema():
    # Create an in-memory database to test the schema
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(bind=engine)

    # Try to create a thread with user_id to test if model works
    from sqlalchemy.orm import Session
    session = Session(bind=engine)

    try:
        # Create a mock user first
        from app.src.models.user import User as UserModel
        user = UserModel(username='test_user', hashed_password='hashed')
        session.add(user)
        session.commit()
        print(f"User created with ID: {user.id}")

        # Now create a thread with user_id
        from app.src.models.thread import Thread as ThreadModel
        thread = ThreadModel(name='Test Thread', user_id=user.id)
        session.add(thread)
        session.commit()
        print(f"Thread created successfully with ID: {thread.id} and user_id: {thread.user_id}")

        # Test the get_by_user_id functionality
        from app.src.services.thread import thread_service
        from app.src.schema import ThreadCreate
        
        # Create another thread for the same user
        thread_in = ThreadCreate(name="Another Test Thread", user_id=user.id)
        created_thread = thread_service.create(session, thread_in)
        print(f"Created thread via service: {created_thread.name} with ID {created_thread.id}")
        
        # Get threads by user_id
        user_threads = thread_service.get_by_user_id(session, user_id=user.id)
        print(f"Found {len(user_threads)} threads for user {user.id}")
        
        for t in user_threads:
            print(f"  - Thread: {t.name} (ID: {t.id})")
        
        print('All tests passed!')
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    test_schema()