from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.database.session import get_session
from app.modules.role.schema.role_schema import RoleCreate
from app.modules.role.service.role_service import RoleService

role = APIRouter(
    prefix="/role",
    tags=["role"],
)

role_service = RoleService()


@role.post("", status_code=status.HTTP_201_CREATED)
def create(payload: RoleCreate, session: Session = Depends(get_session)):
    return role_service.create(session, payload)


@role.get("", status_code=status.HTTP_200_OK)
def get_all(session: Session = Depends(get_session)):
    return role_service.get_all(session)

@role.get("", status_code=status.HTTP_200_OK)
def get_by_id(session: Session = Depends(get_session)):
    return role_service.get_all(session)

@role.get("/{role_id}", status_code=status.HTTP_200_OK)
def get_by_role(role_id: int, session: Session = Depends(get_session)):
    return role_service.get_by_id(session, role_id)