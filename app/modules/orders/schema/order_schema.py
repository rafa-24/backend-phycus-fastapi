from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from sqlmodel import SQLModel

PaymentStatus = Literal["pending", "approved", "rejected", "voided"]
FulfillmentStatus = Literal[
    "awaiting_payment",
    "ready",
    "preparing",
    "dispatched",
    "invoiced",
    "cancelled",
]


class OrderItemCreate(SQLModel):
    product_id: Optional[int] = None
    product_name: str
    product_image_url: Optional[str] = None
    unit_price: Decimal
    quantity: int
    discount_percent: Decimal = Decimal("0")


class OrderCreate(SQLModel):
    """Crea el pedido pendiente y prepara el pago Bold (order_id + firma)."""

    store_id: int
    order_identifier: str
    items: list[OrderItemCreate]
    delivery_address: str
    delivery_neighborhood: str
    delivery_locality: Optional[str] = None
    delivery_city: Optional[str] = None
    tariff_id: Optional[int] = None
    shipping_cost: Decimal = Decimal("0")
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    currency: str = "COP"


class OrderFulfillmentUpdate(SQLModel):
    fulfillment_status: FulfillmentStatus
    notes: Optional[str] = None


class OrderStatusUpdate(SQLModel):
    """
    Actualización manual del embudo (panel Pedidos).
    Permite marcar pago aprobado sin webhook y avanzar surtido / contacto.
    """

    payment_status: Optional[PaymentStatus] = None
    fulfillment_status: Optional[FulfillmentStatus] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    notes: Optional[str] = None
    # Etapa del embudo: pending_payment | ready | preparing | dispatched | invoiced | cancelled
    funnel_stage: Optional[str] = None


class OrderItemResponse(SQLModel):
    id: int
    order_id: int
    product_id: Optional[int]
    product_name: str
    product_image_url: Optional[str]
    unit_price: Decimal
    quantity: int
    line_total: Decimal
    discount_percent: Decimal


class OrderResponse(SQLModel):
    id: int
    store_id: int
    order_identifier: str
    currency: str
    subtotal: Decimal
    shipping_cost: Decimal
    total: Decimal
    integrity_signature: Optional[str]
    payment_status: str
    fulfillment_status: str
    customer_name: Optional[str]
    customer_phone: Optional[str]
    customer_email: Optional[str]
    delivery_address: str
    delivery_neighborhood: str
    delivery_locality: Optional[str]
    delivery_city: Optional[str]
    tariff_id: Optional[int]
    bold_payment_id: Optional[str]
    bold_payment_method: Optional[str]
    bold_event_type: Optional[str]
    paid_at: Optional[datetime]
    notes: Optional[str]
    siigo_invoice_id: Optional[str] = None
    siigo_invoice_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemResponse] = []
