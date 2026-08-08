from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.database.session import get_session
from app.modules.orders.schema.order_schema import (
    OrderCreate,
    OrderFulfillmentUpdate,
    OrderStatusUpdate,
)
from app.modules.orders.service.order_service import OrderService

order = APIRouter(
    prefix="/order",
    tags=["order"],
)

order_service = OrderService()


@order.post("", status_code=status.HTTP_201_CREATED)
def create_checkout(payload: OrderCreate, session: Session = Depends(get_session)):
    """
    Crea el pedido pendiente (productos + domicilio) y genera la
    integrity_signature con la secret_key de Bold en el backend.
    """
    return order_service.create_checkout(session, payload)


@order.get("/store/{store_id}", status_code=status.HTTP_200_OK)
def get_by_store(store_id: int, session: Session = Depends(get_session)):
    return order_service.get_by_store_id(session, store_id)


@order.get("/{order_id}", status_code=status.HTTP_200_OK)
def get_by_id(order_id: int, session: Session = Depends(get_session)):
    return order_service.get_by_id(session, order_id)


@order.patch("/{order_id}/fulfillment", status_code=status.HTTP_200_OK)
def update_fulfillment(
    order_id: int,
    payload: OrderFulfillmentUpdate,
    session: Session = Depends(get_session),
):
    return order_service.update_fulfillment(session, order_id, payload)


@order.patch("/{order_id}/status", status_code=status.HTTP_200_OK)
async def update_status(
    order_id: int,
    payload: OrderStatusUpdate,
    session: Session = Depends(get_session),
):
    """
    Embudo Pedidos: arrastrar a otra columna o confirmar pago a mano
    cuando el webhook de Bold no llegó. Al pasar a Facturado emite factura Siigo.
    """
    return await order_service.update_status(session, order_id, payload)
