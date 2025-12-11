# In app/src/repositories/thread.py
from typing import List, Optional
from sqlalchemy.orm import Session

from app.src.repositories.base import BaseRepository
from app.src.models import Thread as ThreadModel
from app.src.schema import ThreadCreate, ThreadUpdate

class ThreadRepository(BaseRepository[ThreadModel, ThreadCreate, ThreadUpdate]):
    def create(self, db: Session, *, obj_in: ThreadCreate) -> ThreadModel:
        db_obj = ThreadModel(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_by_name(self, db: Session, *, name: str) -> Optional[ThreadModel]:
        """
        Retrieves a thread by its name.
        """
        return db.query(self.model).filter(self.model.name == name).first()

    def search_by_name(
        self, db: Session, *, search_term: str, skip: int = 0, limit: int = 100
    ) -> List[ThreadModel]:
        """
        Performs a case-insensitive search for threads by name.
        """
        if not search_term:
            return self.get_multi(db, skip=skip, limit=limit)

        search_query = f"%{search_term}%"  # Prepare for LIKE query
        query = db.query(self.model).filter(
            self.model.name.ilike(search_query)  # Case-insensitive search
        )
        return query.order_by(self.model.name).offset(skip).limit(limit).all()

    def get_by_user_id(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[ThreadModel]:
        """
        Retrieves threads by user ID.
        """
        return (
            db.query(self.model)
            .filter(self.model.user_id == user_id)
            .order_by(self.model.created_at.desc())  # Order by most recent first
            .offset(skip)
            .limit(limit)
            .all()
        )

# Create a single repository instance for use in your services
thread_repo = ThreadRepository(ThreadModel)