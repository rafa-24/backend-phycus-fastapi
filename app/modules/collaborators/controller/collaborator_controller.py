from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.database.session import get_session
from app.modules.collaborators.schema.collaborator_schema import (
    CollaboratorCreate,
    CollaboratorUpdate,
)
from app.modules.collaborators.service.collaborator_service import CollaboratorService

collaborator = APIRouter(
    prefix="/collaborator",
    tags=["collaborator"],
)

collaborator_service = CollaboratorService()


@collaborator.post("", status_code=status.HTTP_201_CREATED)
def create(payload: CollaboratorCreate, session: Session = Depends(get_session)):
    return collaborator_service.create(session, payload)


@collaborator.get("", status_code=status.HTTP_200_OK)
def get_all(session: Session = Depends(get_session)):
    return collaborator_service.get_all(session)


@collaborator.get("/store/{store_id}", status_code=status.HTTP_200_OK)
def get_by_store(store_id: int, session: Session = Depends(get_session)):
    return collaborator_service.get_by_store_id(session, store_id)


@collaborator.get("/user/{user_id}", status_code=status.HTTP_200_OK)
def get_by_user(user_id: int, session: Session = Depends(get_session)):
    return collaborator_service.get_by_user_id(session, user_id)


@collaborator.get("/{collaborator_id}", status_code=status.HTTP_200_OK)
def get_by_id(collaborator_id: int, session: Session = Depends(get_session)):
    return collaborator_service.get_by_id(session, collaborator_id)


@collaborator.put("/{collaborator_id}", status_code=status.HTTP_200_OK)
def update(
    collaborator_id: int,
    payload: CollaboratorUpdate,
    session: Session = Depends(get_session),
):
    return collaborator_service.update(session, collaborator_id, payload)


@collaborator.delete("/{collaborator_id}", status_code=status.HTTP_200_OK)
def delete(collaborator_id: int, session: Session = Depends(get_session)):
    return collaborator_service.delete(session, collaborator_id)
