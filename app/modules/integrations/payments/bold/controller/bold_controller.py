import json

from fastapi import APIRouter, Depends, Request, status
from sqlmodel import Session

from app.database.session import get_session
from app.modules.integrations.payments.bold.schema.paymentConfigPayload_model import (
    BoldIntegrityRequest,
    PaymentConfigCreate,
    PaymentConfigUpdate,
)
from app.modules.integrations.payments.bold.service.bold_service import BoldService

bold = APIRouter(
    prefix="/bold",
    tags=["bold"],
)

payment_config_bold = BoldService()


@bold.post("", status_code=status.HTTP_201_CREATED)
def create(payload: PaymentConfigCreate, session: Session = Depends(get_session)):
    return payment_config_bold.create_button_payment(session, payload)


@bold.post("/webhook", status_code=status.HTTP_200_OK)
async def bold_webhook(request: Request, session: Session = Depends(get_session)):
    """
    Endpoint que registras en el panel de Bold → Integraciones → Webhook.

    Bold envía SALE_APPROVED / SALE_REJECTED / VOID_* y aquí actualizamos
    el payment_status (y fulfillment) del pedido en Phycus.
    Responde 200 rápido para evitar reintentos.
    """
    raw_body = await request.body()
    signature = request.headers.get("x-bold-signature") or request.headers.get(
        "X-Bold-Signature"
    )
    try:
        payload = json.loads(raw_body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        payload = {}

    return payment_config_bold.handle_webhook(
        session,
        raw_body=raw_body,
        signature_header=signature,
        payload=payload if isinstance(payload, dict) else {},
    )


@bold.post("/{store_id}/integrity", status_code=status.HTTP_200_OK)
def create_integrity(
    store_id: int,
    payload: BoldIntegrityRequest,
    session: Session = Depends(get_session),
):
    return payment_config_bold.create_integrity_signature(session, store_id, payload)


@bold.get("/{store_id}", status_code=status.HTTP_200_OK)
def get(store_id: int, session: Session = Depends(get_session)):
    return payment_config_bold.list_payment_details(session, store_id)


@bold.patch(
    "/{store_id}/{payment_detail_id}",
    status_code=status.HTTP_200_OK,
)
def update(
    store_id: int,
    payment_detail_id: int,
    payload: PaymentConfigUpdate,
    session: Session = Depends(get_session),
):
    return payment_config_bold.update_payment_detail(
        session,
        payment_detail_id,
        store_id,
        payload,
    )


@bold.delete(
    "/{store_id}/{payment_detail_id}",
    status_code=status.HTTP_200_OK,
)
def delete(
    store_id: int,
    payment_detail_id: int,
    session: Session = Depends(get_session),
):
    return payment_config_bold.delete_payment_detail(
        session,
        payment_detail_id,
        store_id,
    )
