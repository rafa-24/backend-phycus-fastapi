from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.database.session import get_session
from app.modules.auth.schema.auth_schema import (
    ChangePasswordRequest,
    LoginRequest,
    PasswordRecoveryRequest,
)
from app.modules.auth.service.auth_service import AuthService

auth = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

auth_service = AuthService()


@auth.post("/login", status_code=status.HTTP_200_OK)
def login(payload: LoginRequest, session: Session = Depends(get_session)):
    return auth_service.login(session, payload)


@auth.post("/password-recovery", status_code=status.HTTP_200_OK)
def request_password_recovery(
    payload: PasswordRecoveryRequest, session: Session = Depends(get_session)
):
    return auth_service.request_password_recovery(session, payload)


@auth.post("/change-password", status_code=status.HTTP_200_OK)
def change_password(
    payload: ChangePasswordRequest, session: Session = Depends(get_session)
):
    return auth_service.change_password(session, payload)
