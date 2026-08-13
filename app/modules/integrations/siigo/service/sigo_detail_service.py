import logging
import re
import time
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Optional

import httpx
from sqlmodel import Session

from app.modules.integrations.siigo.models.sigo_details_model import SiigoDetail
from app.modules.integrations.siigo.repository.sigo_detail_repository import (
    SiigoRepository,
)
from app.modules.integrations.siigo.schema.sigo_api_schema import (
    SiigoErrorResponse,
    SiigoTokenSuccess,
)
from app.modules.integrations.siigo.schema.sigo_details_schema import (
    SigoDetailCreate,
    SigoDetailResponse,
    SigoDetailUpdate,
)
from app.modules.integrations.siigo.schema.sigo_sync_schema import (
    SiigoInvoiceResult,
    SiigoSyncProductsResponse,
    SiigoSyncSkippedItem,
)
from app.modules.orders.models.order_model import OrderItems, Orders
from app.modules.products.models.product_model import Products
from app.modules.products.repository.product_repository import ProductRepository
from app.modules.products.schema.product_schema import ProductCreate, ProductResponse
from app.modules.products.service.product_service import ProductService
from app.modules.shared.exceptions.app_exceptions import (
    BadRequestException,
    NotFoundException,
)
from app.modules.shared.schemas.api_response import ApiResponse
from app.modules.stores.models.store_model import Stores
from app.modules.stores.repository.store_repository import StoreRepository

logger = logging.getLogger(__name__)

SIIGO_BASE_URL = "https://api.siigo.com"
SIIGO_PARTNER_ID = "phycus"
TOKEN_REFRESH_BUFFER_SECONDS = 120


class SiigoService:
    def __init__(self):
        self.store_repository = StoreRepository()
        self.sigo_repository = SiigoRepository()
        self.product_repository = ProductRepository()
        self.product_service = ProductService()

    def _get_store_or_raise(self, session: Session, store_id: int) -> Stores:
        store = self.store_repository.get_by_id(session, store_id)
        if not store:
            raise NotFoundException(
                "No existe una tienda con el identificador indicado."
            )
        return store

    def _get_detail_for_store_or_raise(
        self,
        session: Session,
        siigo_detail_id: int,
        store_id: int,
    ) -> SiigoDetail:
        self._get_store_or_raise(session, store_id)
        detail = self.sigo_repository.get_by_id(session, siigo_detail_id)
        if not detail:
            raise NotFoundException(
                "No existe una conexión Siigo con ese identificador."
            )
        if detail.store_id != store_id:
            raise BadRequestException(
                "La conexión Siigo no pertenece a la tienda indicada."
            )
        return detail

    def _to_response(self, detail: SiigoDetail) -> SigoDetailResponse:
        return SigoDetailResponse(
            id=detail.id,
            store_id=detail.store_id,
            user_api=detail.user_api,
            has_access_key=bool((detail.access_key or "").strip()),
            status_connection=detail.status_connection,
            token_type=detail.token_type,
            expiration_time=detail.expiration_time,
            created_at=detail.created_at,
        )

    def _apply_token(self, detail: SiigoDetail, token_data: SiigoTokenSuccess) -> None:
        detail.access_token = token_data.access_token
        # Guardamos timestamp absoluto de vencimiento (unix seconds)
        detail.expiration_time = time.time() + float(token_data.expires_in)
        detail.token_type = token_data.token_type or "Bearer"
        detail.status_connection = True

    def _is_token_expired(self, detail: SiigoDetail) -> bool:
        if not (detail.access_token or "").strip():
            return True
        if detail.expiration_time is None:
            return True

        now = time.time()
        exp = float(detail.expiration_time)
        # Compatibilidad: antes se guardaba solo expires_in (ej. 86400)
        if exp < 1_000_000_000:
            created = detail.created_at
            if created.tzinfo is None:
                created = created.replace(tzinfo=UTC)
            return now >= (created.timestamp() + exp - TOKEN_REFRESH_BUFFER_SECONDS)
        return now >= (exp - TOKEN_REFRESH_BUFFER_SECONDS)

    async def generate_token_sigo(
        self, user: str, access_key: str
    ) -> SiigoTokenSuccess:
        url = f"{SIIGO_BASE_URL}/auth"
        headers = {
            "Content-Type": "application/json",
            "Partner-Id": SIIGO_PARTNER_ID,
        }
        payload = {
            "username": user.strip(),
            "access_key": access_key.strip(),
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=20.0,
                )
                response.raise_for_status()
                return SiigoTokenSuccess.model_validate(response.json())
            except httpx.HTTPStatusError as exc:
                message = "El usuario o la llave de acceso de Siigo son incorrectos."
                try:
                    error_json = exc.response.json()
                    parsed = SiigoErrorResponse.model_validate(error_json)
                    details = [err.message for err in parsed.errors if err.message]
                    if details:
                        message = details[0]
                except Exception:
                    pass
                raise BadRequestException(message) from exc
            except httpx.RequestError as exc:
                raise BadRequestException(
                    f"No se pudo conectar con el servicio de Siigo: {exc}"
                ) from exc

    def _parse_siigo_error(self, response: httpx.Response, fallback: str) -> str:
        try:
            error_json = response.json()
            parsed = SiigoErrorResponse.model_validate(error_json)
            details = [err.message for err in parsed.errors if err.message]
            if details:
                return details[0]
            if isinstance(error_json, dict) and error_json.get("Message"):
                return str(error_json["Message"])
        except Exception:
            text = (response.text or "").strip()
            if text:
                return text[:280]
        return fallback

    async def _ensure_connected_detail(
        self, session: Session, store_id: int
    ) -> SiigoDetail:
        self._get_store_or_raise(session, store_id)
        detail = self.sigo_repository.get_latest_by_store(session, store_id)
        if (
            not detail
            or not detail.status_connection
            or not (detail.user_api or "").strip()
            or not (detail.access_key or "").strip()
        ):
            raise BadRequestException(
                "Debes conectar tu cuenta de Siigo en Integraciones "
                "antes de sincronizar productos o emitir facturas."
            )

        if self._is_token_expired(detail):
            token_data = await self.generate_token_sigo(
                detail.user_api or "",
                detail.access_key or "",
            )
            self._apply_token(detail, token_data)
            detail = self.sigo_repository.update(session, detail)
            logger.info("Token Siigo renovado para store_id=%s", store_id)

        return detail

    def _auth_headers(self, detail: SiigoDetail) -> dict[str, str]:
        token_type = (detail.token_type or "Bearer").strip() or "Bearer"
        token = (detail.access_token or "").strip()
        return {
            "Content-Type": "application/json",
            "Partner-Id": SIIGO_PARTNER_ID,
            "Authorization": f"{token_type} {token}",
        }

    async def _siigo_request(
        self,
        session: Session,
        detail: SiigoDetail,
        method: str,
        path: str,
        *,
        params: Optional[dict[str, Any]] = None,
        json_body: Optional[dict[str, Any]] = None,
        timeout: float = 45.0,
    ) -> Any:
        url = f"{SIIGO_BASE_URL}{path}"

        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                url,
                headers=self._auth_headers(detail),
                params=params,
                json=json_body,
                timeout=timeout,
            )

            # Token inválido/vencido: renovar una vez y reintentar
            if response.status_code in {401, 403}:
                token_data = await self.generate_token_sigo(
                    detail.user_api or "",
                    detail.access_key or "",
                )
                self._apply_token(detail, token_data)
                self.sigo_repository.update(session, detail)
                response = await client.request(
                    method,
                    url,
                    headers=self._auth_headers(detail),
                    params=params,
                    json=json_body,
                    timeout=timeout,
                )

            if response.status_code >= 400:
                message = self._parse_siigo_error(
                    response,
                    f"Error Siigo ({response.status_code}) en {path}.",
                )
                raise BadRequestException(message)

            if response.status_code == 204 or not response.content:
                return None
            return response.json()

    async def create_connection_sigo(
        self,
        session: Session,
        payload: SigoDetailCreate,
    ):
        store = self._get_store_or_raise(session, payload.store_id)

        user_api = payload.user_api.strip()
        access_key = payload.access_key.strip()
        if not user_api or "@" not in user_api:
            raise BadRequestException(
                "Ingresa el correo/usuario de tu cuenta Siigo."
            )

        existing = self.sigo_repository.get_latest_by_store(session, store.id)
        if not access_key and existing and (existing.access_key or "").strip():
            access_key = (existing.access_key or "").strip()

        if not access_key:
            raise BadRequestException(
                "Ingresa la llave de acceso (access key) de Siigo."
            )

        token_data = await self.generate_token_sigo(user_api, access_key)

        if existing:
            existing.user_api = user_api
            existing.access_key = access_key
            self._apply_token(existing, token_data)
            saved = self.sigo_repository.update(session, existing)
            return ApiResponse(
                message="Conexión con Siigo actualizada correctamente.",
                data=self._to_response(saved),
            )

        detail = SiigoDetail(
            store_id=store.id,
            user_api=user_api,
            access_key=access_key,
        )
        self._apply_token(detail, token_data)
        created = self.sigo_repository.create(session, detail)
        return ApiResponse(
            message="Conexión con Siigo exitosa.",
            data=self._to_response(created),
        )

    def list_connections(self, session: Session, store_id: int):
        self._get_store_or_raise(session, store_id)
        details = self.sigo_repository.get_all(session, store_id)
        if not details:
            return ApiResponse(
                message="Aún no tienes conexión con Siigo.",
                data=[],
            )
        return ApiResponse(
            message="Conexiones Siigo obtenidas correctamente.",
            data=[self._to_response(item) for item in details],
        )

    def get_connection(self, session: Session, store_id: int):
        """Devuelve la conexión más reciente de la tienda (o null)."""
        self._get_store_or_raise(session, store_id)
        detail = self.sigo_repository.get_latest_by_store(session, store_id)
        if not detail:
            return ApiResponse(
                message="Esta tienda no tiene conexión Siigo.",
                data=None,
            )
        return ApiResponse(
            message="Conexión Siigo obtenida correctamente.",
            data=self._to_response(detail),
        )

    async def update_connection(
        self,
        session: Session,
        store_id: int,
        siigo_detail_id: int,
        payload: SigoDetailUpdate,
    ):
        detail = self._get_detail_for_store_or_raise(
            session, siigo_detail_id, store_id
        )
        update_data = payload.model_dump(exclude_unset=True)
        if not update_data:
            raise BadRequestException("No se enviaron datos para actualizar.")

        user_api = (update_data.get("user_api") or detail.user_api or "").strip()
        access_key = (
            update_data.get("access_key") or detail.access_key or ""
        ).strip()
        if not user_api or not access_key:
            raise BadRequestException(
                "Se requieren usuario y access key para reconectar Siigo."
            )

        token_data = await self.generate_token_sigo(user_api, access_key)
        detail.user_api = user_api
        if update_data.get("access_key"):
            detail.access_key = access_key
        self._apply_token(detail, token_data)

        updated = self.sigo_repository.update(session, detail)
        return ApiResponse(
            message="Conexión Siigo actualizada correctamente.",
            data=self._to_response(updated),
        )

    def delete_connection(
        self,
        session: Session,
        store_id: int,
        siigo_detail_id: int,
    ):
        detail = self._get_detail_for_store_or_raise(
            session, siigo_detail_id, store_id
        )
        response_data = self._to_response(detail)
        self.sigo_repository.delete(session, detail)
        return ApiResponse(
            message="Conexión Siigo eliminada correctamente.",
            data=response_data,
        )

    def _extract_price(self, raw: dict[str, Any]) -> Decimal | None:
        prices = raw.get("prices") or []
        for price_block in prices:
            for item in price_block.get("price_list") or []:
                value = item.get("value")
                if value is None:
                    continue
                try:
                    amount = Decimal(str(value))
                    if amount > 0:
                        return amount
                except Exception:
                    continue
        return None

    def _extract_ean(self, raw: dict[str, Any]) -> str | None:
        extra = raw.get("additional_fields") or {}
        barcode = extra.get("barcode") if isinstance(extra, dict) else None
        if barcode is None:
            return None
        text = str(barcode).strip()
        return text[:80] if text else None


# Refcatorizar
    async def _fetch_all_siigo_products(
        self, session: Session, detail: SiigoDetail
    ) -> list[dict[str, Any]]:
        page = 1
        page_size = 100
        results: list[dict[str, Any]] = []

        # Se puede manejar mejor la peticion en siigo

        # y se pueden guardar de manera mas optima los productos

        while True:
            data = await self._siigo_request(
                session,
                detail,
                "GET",
                "/v1/products",
                params={"page": page, "page_size": page_size},
            )
            batch = []
            if isinstance(data, dict):
                batch = data.get("results") or []
            elif isinstance(data, list):
                batch = data

            results.extend(batch)

            pagination = data.get("pagination") if isinstance(data, dict) else None
            total = None
            if isinstance(pagination, dict):
                total = pagination.get("total_results")

            if not batch:
                break
            if total is not None and len(results) >= int(total):
                break
            if len(batch) < page_size:
                break
            page += 1
            if page > 200:
                break

        return results

    async def sync_products(self, session: Session, store_id: int):
        """
        Trae el inventario de Siigo y lo crea/actualiza en Phycus
        usando el flujo de create/update de productos.
        """
        detail = await self._ensure_connected_detail(session, store_id)
        raw_products = await self._fetch_all_siigo_products(session, detail)

        created_count = 0
        updated_count = 0
        skipped: list[SiigoSyncSkippedItem] = []
        synced: list[ProductResponse] = []

        for raw in raw_products:
            siigo_id = str(raw.get("id") or "").strip() or None
            siigo_code = str(raw.get("code") or "").strip() or None
            name = str(raw.get("name") or "").strip()
            ean = self._extract_ean(raw)
            price = self._extract_price(raw)
            stock_raw = raw.get("available_quantity")
            try:
                stock = int(stock_raw) if stock_raw is not None else None
            except (TypeError, ValueError):
                stock = None
            active = bool(raw.get("active", True))
            description = raw.get("description")
            description = str(description).strip() if description else None

            if not siigo_code:
                skipped.append(
                    SiigoSyncSkippedItem(
                        siigo_id=siigo_id,
                        siigo_code=siigo_code,
                        name=name or None,
                        reason="El producto no tiene código (code) en Siigo.",
                    )
                )
                continue
            if not name:
                skipped.append(
                    SiigoSyncSkippedItem(
                        siigo_id=siigo_id,
                        siigo_code=siigo_code,
                        name=None,
                        reason="El producto no tiene nombre en Siigo.",
                    )
                )
                continue
            if price is None:
                skipped.append(
                    SiigoSyncSkippedItem(
                        siigo_id=siigo_id,
                        siigo_code=siigo_code,
                        name=name,
                        reason="El producto no tiene precio válido en Siigo.",
                    )
                )
                continue

            existing = None
            if siigo_id:
                existing = self.product_repository.get_by_siigo_id(
                    session, store_id, siigo_id
                )
            if not existing:
                existing = self.product_repository.get_by_siigo_code(
                    session, store_id, siigo_code
                )

            if existing:
                existing.name = name[:255]
                existing.description = description
                existing.price = price
                existing.stock = stock
                existing.is_active = active
                existing.siigo_id = siigo_id
                existing.siigo_code = siigo_code
                existing.ean = ean
                saved = self.product_repository.update(session, existing)
                updated_count += 1
                synced.append(ProductResponse.model_validate(saved))
                continue

            created_response = self.product_service.create(
                session,
                ProductCreate(
                    store_id=store_id,
                    name=name[:255],
                    description=description,
                    price=price,
                    is_active=active,
                    stock=stock,
                    siigo_id=siigo_id,
                    siigo_code=siigo_code,
                    ean=ean,
                ),
            )
            created_count += 1
            if created_response.data:
                synced.append(created_response.data)

        summary = SiigoSyncProductsResponse(
            fetched=len(raw_products),
            created=created_count,
            updated=updated_count,
            skipped=len(skipped),
            skipped_items=skipped[:40],
            products=synced,
        )
        return ApiResponse(
            message=(
                f"Sincronización Siigo: {created_count} creados, "
                f"{updated_count} actualizados, {len(skipped)} omitidos."
            ),
            data=summary,
        )

    async def _resolve_document_type_id(
        self, session: Session, detail: SiigoDetail
    ) -> int:
        data = await self._siigo_request(
            session,
            detail,
            "GET",
            "/v1/document-types",
            params={"type": "FV"},
        )
        items = data if isinstance(data, list) else []
        for item in items:
            if item.get("active", True) is False:
                continue
            doc_id = item.get("id")
            if doc_id is not None:
                return int(doc_id)
        raise BadRequestException(
            "No se encontró un tipo de comprobante FV activo en Siigo. "
            "Configura una factura de venta en Siigo Nube."
        )

    async def _resolve_seller_id(
        self, session: Session, detail: SiigoDetail
    ) -> int:
        data = await self._siigo_request(
            session,
            detail,
            "GET",
            "/v1/users",
            params={"page": 1, "page_size": 25},
        )
        results = []
        if isinstance(data, dict):
            results = data.get("results") or []
        elif isinstance(data, list):
            results = data

        for user in results:
            if user.get("active", True) is False:
                continue
            user_id = user.get("id")
            if user_id is not None:
                return int(user_id)

        raise BadRequestException(
            "No se encontró un vendedor/usuario activo en Siigo. "
            "Verifica los usuarios de tu cuenta Siigo."
        )

    async def _resolve_payment_type_id(
        self, session: Session, detail: SiigoDetail
    ) -> tuple[int, bool]:
        data = await self._siigo_request(
            session,
            detail,
            "GET",
            "/v1/payment-types",
            params={"document_type": "FV"},
        )
        items = data if isinstance(data, list) else []
        # Preferir contado (sin due_date)
        for item in items:
            if item.get("active", True) is False:
                continue
            if item.get("due_date") is True:
                continue
            payment_id = item.get("id")
            if payment_id is not None:
                return int(payment_id), False

        for item in items:
            if item.get("active", True) is False:
                continue
            payment_id = item.get("id")
            if payment_id is not None:
                return int(payment_id), bool(item.get("due_date"))

        raise BadRequestException(
            "No se encontró una forma de pago activa para facturas (FV) en Siigo."
        )

    def _split_customer_name(self, full_name: str | None) -> tuple[str, str]:
        parts = [p for p in (full_name or "").strip().split() if p]
        if not parts:
            return "Cliente", "Phycus"
        if len(parts) == 1:
            return parts[0][:100], "Cliente"
        return parts[0][:100], " ".join(parts[1:])[:100]

    def _customer_identification(self, order: Orders) -> str:
        digits = re.sub(r"\D", "", order.customer_phone or "")
        if len(digits) >= 6:
            return digits[:50]
        # Consumidor final Colombia (fallback)
        return "222222222222"

    def _build_invoice_customer(self, order: Orders) -> dict[str, Any]:
        first_name, last_name = self._split_customer_name(order.customer_name)
        phone_digits = re.sub(r"\D", "", order.customer_phone or "")
        address = (order.delivery_address or "Dirección no registrada").strip()[:256]
        customer: dict[str, Any] = {
            "person_type": "Person",
            "id_type": "13",
            "identification": self._customer_identification(order),
            "branch_office": 0,
            "name": [first_name, last_name],
            "address": {
                "address": address or "Dirección no registrada",
                "city": {
                    "country_code": "Co",
                    "state_code": "11",
                    "city_code": "11001",
                },
            },
            "contacts": [
                {
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": (order.customer_email or "cliente@phycus.app").strip(),
                }
            ],
        }
        if phone_digits:
            customer["phones"] = [{"number": phone_digits[:10]}]
        return customer

    async def create_invoice_for_order(
        self,
        session: Session,
        order: Orders,
        items: list[OrderItems],
    ) -> SiigoInvoiceResult:
        """
        Emite factura de venta en Siigo para un pedido Phycus.
        Requiere productos sincronizados (siigo_code).
        """
        if order.siigo_invoice_id:
            return SiigoInvoiceResult(
                invoice_id=order.siigo_invoice_id,
                invoice_name=order.siigo_invoice_name,
            )

        detail = await self._ensure_connected_detail(session, order.store_id)

        if not items:
            raise BadRequestException(
                "El pedido no tiene ítems para facturar en Siigo."
            )

        invoice_items: list[dict[str, Any]] = []
        missing: list[str] = []
        total = Decimal("0")

        for item in items:
            product: Products | None = None
            if item.product_id is not None:
                product = self.product_repository.get_by_id(session, item.product_id)

            code = (product.siigo_code if product else None) or None
            if not code:
                missing.append(item.product_name)
                continue

            price = Decimal(str(item.unit_price or 0))
            qty = int(item.quantity or 0)
            if qty <= 0 or price < 0:
                continue

            line: dict[str, Any] = {
                "code": code,
                "description": item.product_name[:200],
                "quantity": qty,
                "price": float(price),
            }
            discount = Decimal(str(item.discount_percent or 0))
            if discount > 0:
                line["discount"] = float(discount)

            invoice_items.append(line)
            line_total = price * qty
            if discount > 0:
                line_total = line_total * (Decimal("1") - discount / Decimal("100"))
            total += line_total

        if missing:
            names = ", ".join(missing[:5])
            extra = f" (+{len(missing) - 5} más)" if len(missing) > 5 else ""
            raise BadRequestException(
                "Hay productos sin código Siigo. Sincroniza el inventario "
                f"con Siigo antes de facturar. Faltan: {names}{extra}."
            )

        if not invoice_items:
            raise BadRequestException(
                "No hay ítems válidos para emitir la factura en Siigo."
            )

        document_id = await self._resolve_document_type_id(session, detail)
        seller_id = await self._resolve_seller_id(session, detail)
        payment_id, needs_due = await self._resolve_payment_type_id(session, detail)

        today = datetime.now(UTC).date().isoformat()
        payment: dict[str, Any] = {
            "id": payment_id,
            "value": float(round(total, 2)),
        }
        if needs_due:
            payment["due_date"] = today

        observations = (
            f"Pedido Phycus {order.order_identifier}. "
            f"Barrio: {order.delivery_neighborhood or '-'}. "
            f"Domicilio: {order.shipping_cost}."
        )

        payload = {
            "document": {"id": document_id},
            "date": today,
            "customer": self._build_invoice_customer(order),
            "seller": seller_id,
            "observations": observations[:4000],
            "items": invoice_items,
            "payments": [payment],
        }

        data = await self._siigo_request(
            session,
            detail,
            "POST",
            "/v1/invoices",
            json_body=payload,
            timeout=60.0,
        )

        invoice_id = None
        invoice_name = None
        number = None
        if isinstance(data, dict):
            invoice_id = str(data.get("id") or "") or None
            invoice_name = str(data.get("name") or "") or None
            number = data.get("number")

        if not invoice_id and not invoice_name:
            raise BadRequestException(
                "Siigo no devolvió el identificador de la factura."
            )

        return SiigoInvoiceResult(
            invoice_id=invoice_id,
            invoice_name=invoice_name,
            number=int(number) if number is not None else None,
        )
