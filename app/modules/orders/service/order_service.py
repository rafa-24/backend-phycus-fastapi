import hashlib
import logging
from datetime import UTC, datetime
from decimal import Decimal

from sqlmodel import Session

from app.modules.integrations.payments.bold.repository.bold_repository import (
    BoldRepository,
)
from app.modules.integrations.siigo.service.sigo_detail_service import SiigoService
from app.modules.orders.models.order_model import OrderItems, Orders
from app.modules.orders.repository.order_repository import OrderRepository
from app.modules.orders.schema.order_schema import (
    OrderCreate,
    OrderFulfillmentUpdate,
    OrderItemCreate,
    OrderItemResponse,
    OrderResponse,
    OrderStatusUpdate,
)
from app.modules.shared.exceptions.app_exceptions import (
    BadRequestException,
    NotFoundException,
)
from app.modules.shared.schemas.api_response import ApiResponse
from app.modules.stores.repository.store_repository import StoreRepository

logger = logging.getLogger(__name__)

# Mapeo evento Bold (type del webhook) → payment_status interno
BOLD_EVENT_TO_PAYMENT = {
    "SALE_APPROVED": "approved",
    "SALE_REJECTED": "rejected",
    "VOID_APPROVED": "voided",
    "VOID_REJECTED": "rejected",
}


class OrderService:
    def __init__(self):
        self.order_repository = OrderRepository()
        self.store_repository = StoreRepository()
        self.bold_repository = BoldRepository()
        self.siigo_service = SiigoService()

    def _get_store_or_raise(self, session: Session, store_id: int):
        store = self.store_repository.get_by_id(session, store_id)
        if not store:
            raise NotFoundException("No existe una tienda con ese identificador.")
        return store

    def _get_order_or_raise(self, session: Session, order_id: int) -> Orders:
        order = self.order_repository.get_by_id(session, order_id)
        if not order:
            raise NotFoundException("No existe un pedido con ese identificador.")
        return order

    def _build_integrity_signature(
        self,
        order_identifier: str,
        amount: int,
        currency: str,
        secret_key: str,
    ) -> str:
        """
        Genera el hash de integridad Bold EN EL BACKEND.

        Fórmula oficial Bold (botón de pagos):
            SHA256( orderId + amount + currency + secretKey )

        - orderId: el order_identifier que nosotros creamos (ej. ORD1722...)
        - amount: total en enteros (COP sin decimales)
        - currency: normalmente "COP"
        - secretKey: secret_key_bold guardada en PaymentDetail (NUNCA se devuelve en GET)

        Por qué en backend:
        Si firmáramos en el navegador, cualquiera podría ver la secreta y
        falsificar montos. Aquí la secreta solo vive en la BD y se usa para
        calcular el hex digest que sí puede viajar al front / a Bold.
        """
        concatenated = f"{order_identifier}{amount}{currency}{secret_key}"
        return hashlib.sha256(concatenated.encode("utf-8")).hexdigest()

    def _to_response(self, session: Session, order: Orders) -> OrderResponse:
        items = self.order_repository.get_items_by_order_id(session, order.id)
        return OrderResponse(
            id=order.id,
            store_id=order.store_id,
            order_identifier=order.order_identifier,
            currency=order.currency,
            subtotal=order.subtotal,
            shipping_cost=order.shipping_cost,
            total=order.total,
            integrity_signature=order.integrity_signature,
            payment_status=order.payment_status,
            fulfillment_status=order.fulfillment_status,
            customer_name=order.customer_name,
            customer_phone=order.customer_phone,
            customer_email=order.customer_email,
            delivery_address=order.delivery_address,
            delivery_neighborhood=order.delivery_neighborhood,
            delivery_locality=order.delivery_locality,
            delivery_city=order.delivery_city,
            tariff_id=order.tariff_id,
            bold_payment_id=order.bold_payment_id,
            bold_payment_method=order.bold_payment_method,
            bold_event_type=order.bold_event_type,
            paid_at=order.paid_at,
            notes=order.notes,
            siigo_invoice_id=order.siigo_invoice_id,
            siigo_invoice_name=order.siigo_invoice_name,
            created_at=order.created_at,
            updated_at=order.updated_at,
            items=[
                OrderItemResponse(
                    id=item.id,
                    order_id=item.order_id,
                    product_id=item.product_id,
                    product_name=item.product_name,
                    product_image_url=item.product_image_url,
                    unit_price=item.unit_price,
                    quantity=item.quantity,
                    line_total=item.line_total,
                    discount_percent=item.discount_percent,
                )
                for item in items
            ],
        )

    def create_checkout(self, session: Session, payload: OrderCreate):
        """
        Persiste el pedido (productos + domicilio) en estado pending,
        firma el monto con la secret_key de la tienda y devuelve todo
        listo para abrir el botón Bold.
        """
        self._get_store_or_raise(session, payload.store_id)

        order_identifier = payload.order_identifier.strip()
        if not order_identifier or len(order_identifier) > 60:
            raise BadRequestException("El order_identifier de Bold no es válido.")

        existing = self.order_repository.get_by_identifier(session, order_identifier)
        if existing:
            raise BadRequestException(
                "Ese identificador de pedido ya fue usado. Genera uno nuevo."
            )

        if not payload.items:
            raise BadRequestException("El pedido debe tener al menos un producto.")

        if not payload.delivery_address.strip():
            raise BadRequestException("La dirección de entrega es obligatoria.")

        if not payload.delivery_neighborhood.strip():
            raise BadRequestException("El barrio de entrega es obligatorio.")

        name = (payload.customer_name or "").strip()
        phone = (payload.customer_phone or "").strip()
        email = (payload.customer_email or "").strip()
        if len(name) < 2:
            raise BadRequestException("El nombre de quien recibe es obligatorio.")
        if len(phone) < 7:
            raise BadRequestException("El teléfono de contacto es obligatorio.")
        if "@" not in email or "." not in email:
            raise BadRequestException("El correo de contacto no es válido.")

        subtotal = Decimal("0")
        prepared_items: list[tuple[OrderItemCreate, Decimal]] = []

        for raw in payload.items:
            if raw.quantity < 1:
                raise BadRequestException(
                    f"Cantidad inválida para {raw.product_name}."
                )
            unit = Decimal(str(raw.unit_price))
            if unit < 0:
                raise BadRequestException(
                    f"Precio inválido para {raw.product_name}."
                )
            line_total = unit * raw.quantity
            subtotal += line_total
            prepared_items.append((raw, line_total))

        shipping = Decimal(str(payload.shipping_cost or 0))
        if shipping < 0:
            raise BadRequestException("El costo de domicilio no puede ser negativo.")

        total = subtotal + shipping
        amount_int = int(total)
        if amount_int < 1000:
            raise BadRequestException("El monto mínimo de Bold es 1000 COP.")

        currency = (payload.currency or "COP").strip().upper()

        # Carga la config Bold de la tienda para firmar con la secreta
        payment_details = self.bold_repository.get_all(session, payload.store_id)
        if not payment_details:
            raise BadRequestException(
                "Esta tienda aún no tiene configuración de pagos Bold."
            )
        payment_detail = sorted(
            payment_details,
            key=lambda item: item.created_at or item.id or 0,
            reverse=True,
        )[0]
        secret = (payment_detail.secret_key_bold or "").strip()
        if not secret:
            raise BadRequestException(
                "La tienda no tiene una llave secreta Bold configurada."
            )

        # Hash: SHA256(orderId + amount + currency + secretKey)
        signature = self._build_integrity_signature(
            order_identifier,
            amount_int,
            currency,
            secret,
        )

        order = Orders(
            store_id=payload.store_id,
            order_identifier=order_identifier,
            currency=currency,
            subtotal=subtotal,
            shipping_cost=shipping,
            total=total,
            integrity_signature=signature,
            payment_status="pending",
            fulfillment_status="awaiting_payment",
            customer_name=name,
            customer_phone=phone,
            customer_email=email,
            delivery_address=payload.delivery_address.strip(),
            delivery_neighborhood=payload.delivery_neighborhood.strip(),
            delivery_locality=(payload.delivery_locality or "").strip() or None,
            delivery_city=(payload.delivery_city or "").strip() or None,
            tariff_id=payload.tariff_id,
        )
        created = self.order_repository.create(session, order)

        item_rows = [
            OrderItems(
                order_id=created.id,
                product_id=raw.product_id,
                product_name=raw.product_name.strip(),
                product_image_url=raw.product_image_url,
                unit_price=Decimal(str(raw.unit_price)),
                quantity=raw.quantity,
                line_total=line_total,
                discount_percent=Decimal(str(raw.discount_percent or 0)),
            )
            for raw, line_total in prepared_items
        ]
        self.order_repository.create_items(session, item_rows)

        return ApiResponse(
            message="Pedido creado. Usa order_identifier e integrity_signature en Bold.",
            data=self._to_response(session, created),
        )

    def get_by_store_id(self, session: Session, store_id: int):
        self._get_store_or_raise(session, store_id)
        orders = self.order_repository.get_by_store_id(session, store_id)
        return ApiResponse(
            message="Pedidos obtenidos correctamente.",
            data=[self._to_response(session, order) for order in orders],
        )

    def get_by_id(self, session: Session, order_id: int):
        order = self._get_order_or_raise(session, order_id)
        return ApiResponse(
            message="Pedido obtenido correctamente.",
            data=self._to_response(session, order),
        )

    def update_fulfillment(
        self,
        session: Session,
        order_id: int,
        payload: OrderFulfillmentUpdate,
    ):
        return self.update_status(
            session,
            order_id,
            OrderStatusUpdate(
                fulfillment_status=payload.fulfillment_status,
                notes=payload.notes,
            ),
        )

    async def update_status(
        self,
        session: Session,
        order_id: int,
        payload: OrderStatusUpdate,
    ):
        """
        Mueve el pedido en el embudo del panel.

        Si llega funnel_stage, se mapean payment + fulfillment juntos
        (útil cuando el webhook no llegó y el dueño confirma el cobro a mano).

        Al pasar a ``invoiced`` se emite la factura en Siigo (requiere conexión
        y productos sincronizados con ``siigo_code``).
        """
        order = self._get_order_or_raise(session, order_id)
        previous_fulfillment = order.fulfillment_status

        stage = (payload.funnel_stage or "").strip().lower() or None
        will_invoice = False

        if stage:
            if stage == "cancelled":
                order.fulfillment_status = "cancelled"
                if order.payment_status == "pending":
                    order.payment_status = "rejected"
            else:
                mapped = self._map_funnel_stage(stage)
                order.payment_status = mapped["payment_status"]
                order.fulfillment_status = mapped["fulfillment_status"]
                if mapped["payment_status"] == "approved" and not order.paid_at:
                    order.paid_at = datetime.now(UTC)
                    if not order.bold_event_type:
                        order.bold_event_type = "MANUAL_APPROVED"
                will_invoice = stage == "invoiced"
        else:
            if payload.payment_status is not None:
                order.payment_status = payload.payment_status
                if payload.payment_status == "approved" and not order.paid_at:
                    order.paid_at = datetime.now(UTC)
                    if not order.bold_event_type:
                        order.bold_event_type = "MANUAL_APPROVED"
            if payload.fulfillment_status is not None:
                order.fulfillment_status = payload.fulfillment_status
                will_invoice = payload.fulfillment_status == "invoiced"

        if payload.customer_name is not None:
            order.customer_name = payload.customer_name.strip() or None
        if payload.customer_phone is not None:
            order.customer_phone = payload.customer_phone.strip() or None
        if payload.customer_email is not None:
            order.customer_email = payload.customer_email.strip() or None
        if payload.notes is not None:
            order.notes = payload.notes.strip() or None

        becoming_invoiced = (
            will_invoice
            and previous_fulfillment != "invoiced"
            and order.fulfillment_status == "invoiced"
        )

        if becoming_invoiced and not order.siigo_invoice_id:
            items = self.order_repository.get_items_by_order_id(session, order.id)
            invoice = await self.siigo_service.create_invoice_for_order(
                session, order, items
            )
            order.siigo_invoice_id = invoice.invoice_id
            order.siigo_invoice_name = invoice.invoice_name
            note_bits = []
            if order.notes:
                note_bits.append(order.notes)
            if invoice.invoice_name:
                note_bits.append(f"Factura Siigo: {invoice.invoice_name}")
            order.notes = " | ".join(note_bits)[:1000] or order.notes

        order.updated_at = datetime.now(UTC)
        updated = self.order_repository.update(session, order)

        message = "Estado del pedido actualizado."
        if becoming_invoiced and updated.siigo_invoice_name:
            message = (
                f"Pedido facturado en Siigo ({updated.siigo_invoice_name})."
            )
        elif becoming_invoiced and updated.siigo_invoice_id:
            message = "Pedido facturado en Siigo correctamente."

        return ApiResponse(
            message=message,
            data=self._to_response(session, updated),
        )

    def _map_funnel_stage(self, stage: str) -> dict[str, str]:
        mapping = {
            "pending_payment": {
                "payment_status": "pending",
                "fulfillment_status": "awaiting_payment",
            },
            "ready": {
                "payment_status": "approved",
                "fulfillment_status": "ready",
            },
            "preparing": {
                "payment_status": "approved",
                "fulfillment_status": "preparing",
            },
            "dispatched": {
                "payment_status": "approved",
                "fulfillment_status": "dispatched",
            },
            "invoiced": {
                "payment_status": "approved",
                "fulfillment_status": "invoiced",
            },
            "cancelled": {
                "payment_status": "rejected",
                "fulfillment_status": "cancelled",
            },
        }
        if stage not in mapping:
            raise BadRequestException(
                "Etapa de embudo inválida. Usa: pending_payment, ready, "
                "preparing, dispatched, invoiced, cancelled."
            )
        return mapping[stage]

    def apply_bold_webhook_event(
        self,
        session: Session,
        event_type: str,
        payment_id: str | None,
        reference: str | None,
        payment_method: str | None,
    ) -> Orders | None:
        """
        Actualiza el pedido cuando Bold notifica por webhook.

        Flujo:
        1. Bold envía POST a /bold/webhook con type (SALE_APPROVED, etc.)
        2. Buscamos el pedido por metadata.reference (= nuestro order_identifier)
           o por bold_payment_id si ya lo teníamos.
        3. Marcamos payment_status y, si fue aprobado, fulfillment_status=ready
           para que el surtido pueda facturar/despachar.
        """
        order = None
        if reference:
            order = self.order_repository.get_by_identifier(session, reference.strip())
        if order is None and payment_id:
            order = self.order_repository.get_by_bold_payment_id(
                session, payment_id.strip()
            )

        if order is None:
            logger.warning(
                "Webhook Bold sin pedido: type=%s payment_id=%s reference=%s",
                event_type,
                payment_id,
                reference,
            )
            return None

        payment_status = BOLD_EVENT_TO_PAYMENT.get(event_type)
        if not payment_status:
            logger.info("Evento Bold ignorado: %s", event_type)
            return order

        order.payment_status = payment_status
        order.bold_event_type = event_type
        if payment_id:
            order.bold_payment_id = payment_id.strip()
        if payment_method:
            order.bold_payment_method = payment_method.strip()

        if payment_status == "approved":
            order.paid_at = datetime.now(UTC)
            # Listo para que el surtido facture / prepare / despache
            if order.fulfillment_status == "awaiting_payment":
                order.fulfillment_status = "ready"
        elif payment_status in {"rejected", "voided"}:
            if order.fulfillment_status in {"awaiting_payment", "ready"}:
                order.fulfillment_status = "cancelled"

        order.updated_at = datetime.now(UTC)
        return self.order_repository.update(session, order)
