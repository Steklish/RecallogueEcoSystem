from fastapi import APIRouter, Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from app.src.auth.dependencies import get_current_user_from_cookie
from app.src.config import settings
from app.src.database.session import get_db
from app.src.schema import Token
from app.src.utils import security
from app.src.services import auth_service


router = APIRouter(prefix="/test", tags=["Dev"])


@router.get("/info", summary="Вывод информации о пользователе. Использует cookies для получения данных")
def login_for_access_token(db: Session = Depends(get_db), user = Depends(get_current_user_from_cookie)):
    try:
        return {
            "data" : user.__dict__
        }
    except Exception as e:
        return {"error": str(e)}