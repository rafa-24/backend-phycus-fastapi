from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.database.session import get_session
from app.modules.stores.schema.store_schema import StoreCreate, StoreUpdate
from app.modules.stores.service.store_service import StoreService

store = APIRouter(
    prefix="/store",
    tags=["store"],
)

store_service = StoreService()


@store.post("", status_code=status.HTTP_201_CREATED)
def create(payload: StoreCreate, session: Session = Depends(get_session)):
    return store_service.create(session, payload)


@store.get("", status_code=status.HTTP_200_OK)
def get_all(session: Session = Depends(get_session)):
    return store_service.get_all(session)


@store.get("/owner/{owner_id}", status_code=status.HTTP_200_OK)
def get_by_owner(owner_id: int, session: Session = Depends(get_session)):
    return store_service.get_by_owner_id(session, owner_id)


@store.get("/{store_id}", status_code=status.HTTP_200_OK)
def get_by_id(store_id: int, session: Session = Depends(get_session)):
    return store_service.get_by_id(session, store_id)


@store.put("/{store_id}", status_code=status.HTTP_200_OK)
def update(
    store_id: int,
    payload: StoreUpdate,
    session: Session = Depends(get_session),
):
    return store_service.update(session, store_id, payload)
