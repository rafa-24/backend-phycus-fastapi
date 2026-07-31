from fastapi import APIRouter, Depends, status

from sqlmodel import Session
from app.database.session import get_session

from app.modules.users.service.user_service import UserService
from app.modules.users.schema.user_schema import UserCreate


user = APIRouter(
    prefix="/user",
    tags = ["user"]
)

user_service = UserService()

@user.post("/register", status_code= status.HTTP_201_CREATED)
def create(payload: UserCreate, session: Session= Depends(get_session)):
    return user_service.create(session, payload)


@user.get("", status_code=status.HTTP_200_OK)
def get_all(session: Session = Depends(get_session)):
    return user_service.get_all(session)


@user.get("/{user_id}", status_code=status.HTTP_200_OK)
def get_by_id(user_id: int, session: Session = Depends(get_session)):
    return user_service.get_by_id(session, user_id)