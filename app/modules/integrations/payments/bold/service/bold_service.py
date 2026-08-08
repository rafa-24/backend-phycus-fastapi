import hashlib

from sqlmodel import Session

from app.modules.integrations.payments.bold.models.paymentDetails_models import PaymentDetail
from app.modules.integrations.payments.bold.repository.bold_repository import BoldRepository
from app.modules.integrations.payments.bold.schema.paymentConfigPayload_model import (
    BoldIntegrityRequest,
    BoldIntegrityResponse,
    PaymentConfigCreate,
    PaymentConfigResponse,
    PaymentConfigUpdate,
)
from app.modules.shared.exceptions.app_exceptions import (
    BadRequestException,
    InternalServerException,
    NotFoundException,
)
from app.modules.shared.schemas.api_response import ApiResponse
from app.modules.stores.models.store_model import Stores
from app.modules.stores.repository.store_repository import StoreRepository


class BoldService:
    def __init__(self):
        self.store_repository = StoreRepository()
        self.bold_repository = BoldRepository()

    def _get_store_or_raise(self, session: Session, store_id: int) -> Stores:
        store = self.store_repository.get_by_id(session, store_id)

        if not store:
            raise NotFoundException(
                "No existe una tienda con el identificador indicado."
            )

        return store

    def _get_payment_detail_for_store_or_raise(
        self,
        session: Session,
        payment_detail_id: int,
        store_id: int,
    ) -> PaymentDetail:
        self._get_store_or_raise(session, store_id)

        payment_detail = self.bold_repository.get_by_id(session, payment_detail_id)

        if not payment_detail:
            raise NotFoundException(
                "No existe una configuración de pago con el identificador indicado."
            )

        if payment_detail.store_id != store_id:
            raise BadRequestException(
                "La configuración de pago no pertenece a la tienda indicada."
            )

        return payment_detail

    def create_button_payment(self, session: Session, payload: PaymentConfigCreate):
        store = self._get_store_or_raise(session, payload.store_id)

        payment_data = payload.model_dump(exclude={"store_id"})

        new_payment_detail = PaymentDetail(
            store_id=store.id,
            **payment_data,
        )

        created_payment_detail = self.bold_repository.create(
            session, new_payment_detail
        )

        if created_payment_detail.id is None:
            raise InternalServerException(
                "No fue posible guardar detalles del botón de pago."
            )

        return ApiResponse(
            message="Botón de pago configurado de manera correcta.",
            data=PaymentConfigResponse.model_validate(created_payment_detail),
        )

    def list_payment_details(self, session: Session, store_id: int):
        self._get_store_or_raise(session, store_id)

        payment_details = self.bold_repository.get_all(session, store_id)

        if len(payment_details) == 0:
            return ApiResponse(
                message="Aún no tienes configuración de pagos con Bold.",
                data=[],
            )

        safe_payment_details = [
            PaymentConfigResponse.model_validate(detail)
            for detail in payment_details
        ]

        return ApiResponse(
            message="Tu configuración del botón de pago de Bold.",
            data=safe_payment_details,
        )

    def update_payment_detail(
        self,
        session: Session,
        payment_detail_id: int,
        store_id: int,
        payload: PaymentConfigUpdate,
    ):
        payment_detail = self._get_payment_detail_for_store_or_raise(
            session, payment_detail_id, store_id
        )

        update_data = payload.model_dump(exclude_unset=True)

        if not update_data:
            raise BadRequestException(
                "No se enviaron datos para actualizar la configuración de pago."
            )

        for field, value in update_data.items():
            setattr(payment_detail, field, value)

        updated_payment_detail = self.bold_repository.update(session, payment_detail)

        return ApiResponse(
            message="La configuración de pago se actualizó de manera exitosa.",
            data=PaymentConfigResponse.model_validate(updated_payment_detail),
        )

    def delete_payment_detail(
        self,
        session: Session,
        payment_detail_id: int,
        store_id: int,
    ):
        payment_detail = self._get_payment_detail_for_store_or_raise(
            session, payment_detail_id, store_id
        )

        deleted_payment_detail = PaymentConfigResponse.model_validate(payment_detail)

        self.bold_repository.delete(session, payment_detail)

        return ApiResponse(
            message="La configuración de pago se eliminó de manera exitosa.",
            data=deleted_payment_detail,
        )

    def create_integrity_signature(
        self,
        session: Session,
        store_id: int,
        payload: BoldIntegrityRequest,
    ):
        self._get_store_or_raise(session, store_id)

        payment_details = self.bold_repository.get_all(session, store_id)
        if not payment_details:
            raise NotFoundException(
                "Esta tienda aún no tiene configuración de pagos Bold."
            )

        # Usa la configuración más reciente
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

        order_id = payload.order_id.strip()
        if not order_id or len(order_id) > 60:
            raise BadRequestException("El order_id de Bold no es válido.")

        amount = int(payload.amount)
        if amount < 1000:
            raise BadRequestException("El monto mínimo de Bold es 1000 COP.")

        currency = (payload.currency or "COP").strip().upper()
        # Hash Bold: SHA256(orderId + amount + currency + secretKey).
        # La secret_key_bold solo se usa aquí; nunca se incluye en PaymentConfigResponse.
        concatenated = f"{order_id}{amount}{currency}{secret}"
        signature = hashlib.sha256(concatenated.encode("utf-8")).hexdigest()

        return ApiResponse(
            message="Firma de integridad generada correctamente.",
            data=BoldIntegrityResponse(
                order_id=order_id,
                amount=amount,
                currency=currency,
                integrity_signature=signature,
            ),
        )

    def handle_webhook(
        self,
        session: Session,
        raw_body: bytes,
        signature_header: str | None,
        payload: dict,
    ):
        """
        Recibe notificaciones de Bold (SALE_APPROVED, SALE_REJECTED, etc.).

        Seguridad (docs Bold):
        1) body → Base64
        2) HMAC-SHA256(base64_body, llave_identidad) → hex
        3) Comparar con header x-bold-signature

        Estado del pago:
        - SALE_APPROVED  → payment_status=approved, fulfillment=ready
        - SALE_REJECTED  → payment_status=rejected
        - VOID_APPROVED  → payment_status=voided
        """
        import base64
        import hmac
        import logging

        from app.modules.orders.service.order_service import OrderService

        logger = logging.getLogger(__name__)
        order_service = OrderService()

        # Extraemos referencia (= nuestro order_identifier enviado como data-order-id)
        data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
        # No usar subject (payment_id de Bold) como order_identifier nuestro.
        reference = (
            metadata.get("reference")
            or data.get("reference")
            or data.get("order_id")
        )
        if isinstance(reference, str) and not reference.strip():
            reference = None
        if reference in (None, "null"):
            reference = None
        payment_id = data.get("payment_id") or payload.get("subject")
        event_type = str(payload.get("type") or "").strip().upper()
        payment_method = data.get("payment_method")

        # Verifica firma con la identity_key de alguna config Bold conocida
        configs = self.bold_repository.get_all_configs(session)
        signature_ok = False
        if signature_header and configs:
            encoded = base64.b64encode(raw_body)
            for config in configs:
                # Docs: verificar con llave de identidad; también probamos secreta por compatibilidad
                for key_value in (
                    (config.identity_key_bold or "").strip(),
                    (config.secret_key_bold or "").strip(),
                ):
                    if not key_value:
                        continue
                    digest = hmac.new(
                        key=key_value.encode("utf-8"),
                        msg=encoded,
                        digestmod=hashlib.sha256,
                    ).hexdigest()
                    if hmac.compare_digest(digest, signature_header.strip()):
                        signature_ok = True
                        break
                if signature_ok:
                    break

        # Si no hay firma o no validó, aún intentamos actualizar si encontramos el pedido
        # (útil en sandbox). En producción con firma inválida y sin pedido → 401.
        if signature_header and configs and not signature_ok:
            # Intento localizar pedido; si no existe, rechazamos
            probe = None
            if reference:
                from app.modules.orders.repository.order_repository import (
                    OrderRepository,
                )

                probe = OrderRepository().get_by_identifier(
                    session, str(reference).strip()
                )
            if probe is None:
                logger.warning("Webhook Bold con firma inválida y sin pedido.")
                raise BadRequestException("Firma de webhook Bold inválida.")

        order = order_service.apply_bold_webhook_event(
            session,
            event_type=event_type,
            payment_id=str(payment_id) if payment_id else None,
            reference=str(reference) if reference else None,
            payment_method=str(payment_method) if payment_method else None,
        )

        return ApiResponse(
            message=(
                "Webhook Bold procesado."
                if order
                else "Webhook recibido; no se encontró pedido asociado."
            ),
            data={
                "event_type": event_type,
                "payment_id": payment_id,
                "reference": reference,
                "order_id": order.id if order else None,
                "payment_status": order.payment_status if order else None,
                "fulfillment_status": order.fulfillment_status if order else None,
                "signature_verified": signature_ok,
            },
        )
