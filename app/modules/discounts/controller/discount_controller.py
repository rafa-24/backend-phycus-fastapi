from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.database.session import get_session
from app.modules.discounts.schema.discount_schema import DiscountCreate, DiscountUpdate
from app.modules.discounts.service.discount_service import DiscountService

discount = APIRouter(
    prefix="/discount",
    tags=["discount"],
)

discount_service = DiscountService()


@discount.post("", status_code=status.HTTP_201_CREATED)
def create(payload: DiscountCreate, session: Session = Depends(get_session)):
    return discount_service.create(session, payload)


@discount.get("", status_code=status.HTTP_200_OK)
def get_all(session: Session = Depends(get_session)):
    return discount_service.get_all(session)


@discount.get("/store/{store_id}", status_code=status.HTTP_200_OK)
def get_by_store(store_id: int, session: Session = Depends(get_session)):
    return discount_service.get_by_store_id(session, store_id)


@discount.get("/{discount_id}", status_code=status.HTTP_200_OK)
def get_by_id(discount_id: int, session: Session = Depends(get_session)):
    return discount_service.get_by_id(session, discount_id)


@discount.put("/{discount_id}", status_code=status.HTTP_200_OK)
def update(
    discount_id: int,
    payload: DiscountUpdate,
    session: Session = Depends(get_session),
):
    return discount_service.update(session, discount_id, payload)


@discount.delete("/{discount_id}", status_code=status.HTTP_200_OK)
def delete(discount_id: int, session: Session = Depends(get_session)):
    return discount_service.delete(session, discount_id)
