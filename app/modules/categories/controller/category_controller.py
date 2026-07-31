from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.database.session import get_session
from app.modules.categories.schema.category_schema import CategoryCreate, CategoryUpdate
from app.modules.categories.service.category_service import CategoryService

category = APIRouter(
    prefix="/category",
    tags=["category"],
)

category_service = CategoryService()


@category.post("", status_code=status.HTTP_201_CREATED)
def create(payload: CategoryCreate, session: Session = Depends(get_session)):
    return category_service.create(session, payload)


@category.get("", status_code=status.HTTP_200_OK)
def get_all(session: Session = Depends(get_session)):
    return category_service.get_all(session)


@category.get("/store/{store_id}", status_code=status.HTTP_200_OK)
def get_by_store(store_id: int, session: Session = Depends(get_session)):
    return category_service.get_by_store_id(session, store_id)


@category.get("/{category_id}", status_code=status.HTTP_200_OK)
def get_by_id(category_id: int, session: Session = Depends(get_session)):
    return category_service.get_by_id(session, category_id)


@category.put("/{category_id}", status_code=status.HTTP_200_OK)
def update(
    category_id: int,
    payload: CategoryUpdate,
    session: Session = Depends(get_session),
):
    return category_service.update(session, category_id, payload)


@category.delete("/{category_id}", status_code=status.HTTP_200_OK)
def delete(category_id: int, session: Session = Depends(get_session)):
    return category_service.delete(session, category_id)
