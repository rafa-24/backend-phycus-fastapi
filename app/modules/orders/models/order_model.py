from datetime import UTC, datetime
from decimal import Decimal
from typing import Optional

from sqlmodel import Field, SQLModel


class Orders(SQLModel, table=True):
    """
    Pedido de la vitrina pública.

    order_identifier = el order_id que enviamos a Bold (referencia única de la venta).
    integrity_signature = hash SHA256 generado en backend con la secret_key (nunca se expone la secreta).
    payment_status = estado que llega del webhook de Bold (o queda pending hasta entonces).
    fulfillment_status = estado operativo del surtido (despacho / factura).
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    store_id: int = Field(foreign_key="stores.id", index=True)

    # Referencia enviada a Bold (data-order-id). Única por tienda.
    order_identifier: str = Field(max_length=60, index=True)

    # Totales
    currency: str = Field(default="COP", max_length=3)
    subtotal: Decimal = Field(default=0, max_digits=12, decimal_places=2)
    shipping_cost: Decimal = Field(default=0, max_digits=12, decimal_places=2)
    total: Decimal = Field(default=0, max_digits=12, decimal_places=2)

    # Firma de integridad Bold (SHA256). La secret_key NUNCA se guarda aquí ni se devuelve.
    integrity_signature: Optional[str] = Field(default=None, max_length=128)

    # Estados de pago (Bold) y surtido (operación de la tienda)
    # payment: pending | approved | rejected | voided
    payment_status: str = Field(default="pending", max_length=30, index=True)
    # fulfillment: awaiting_payment | ready | preparing | dispatched | invoiced | cancelled
    fulfillment_status: str = Field(
        default="awaiting_payment",
        max_length=30,
        index=True,
    )

    # Datos del comprador / domicilio
    customer_name: Optional[str] = Field(default=None, max_length=255)
    customer_phone: Optional[str] = Field(default=None, max_length=40)
    customer_email: Optional[str] = Field(default=None, max_length=255)
    delivery_address: str = Field(max_length=500)
    delivery_neighborhood: str = Field(max_length=255)
    delivery_locality: Optional[str] = Field(default=None, max_length=255)
    delivery_city: Optional[str] = Field(default=None, max_length=120)
    tariff_id: Optional[int] = Field(default=None)

    # Datos que llegan del webhook Bold
    bold_payment_id: Optional[str] = Field(default=None, max_length=80, index=True)
    bold_payment_method: Optional[str] = Field(default=None, max_length=60)
    bold_event_type: Optional[str] = Field(default=None, max_length=60)
    paid_at: Optional[datetime] = Field(default=None)
    notes: Optional[str] = Field(default=None, max_length=1000)

    # Factura emitida en Siigo al pasar a "Facturado"
    siigo_invoice_id: Optional[str] = Field(default=None, max_length=80)
    siigo_invoice_name: Optional[str] = Field(default=None, max_length=80)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class OrderItems(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.id", index=True)
    product_id: Optional[int] = Field(default=None, foreign_key="products.id")
    product_name: str = Field(max_length=255)
    product_image_url: Optional[str] = Field(default=None, max_length=500)
    unit_price: Decimal = Field(max_digits=12, decimal_places=2)
    quantity: int = Field(ge=1)
    line_total: Decimal = Field(max_digits=12, decimal_places=2)
    discount_percent: Decimal = Field(default=0, max_digits=5, decimal_places=2)
