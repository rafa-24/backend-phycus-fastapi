from decimal import Decimal

from sqlmodel import Session

from app.modules.discounts.models.discount_model import Discounts
from app.modules.discounts.repository.discount_repository import DiscountRepository
from app.modules.discounts.schema.discount_schema import (
    DiscountCreate,
    DiscountResponse,
    DiscountUpdate,
)
from app.modules.helpers.calculate_discount import calculate_discounted_price
from app.modules.products.repository.product_repository import ProductRepository
from app.modules.products.schema.product_schema import ProductUpdate
from app.modules.shared.exceptions.app_exceptions import (
    BadRequestException,
    ConflictException,
    InternalServerException,
    NotFoundException,
)
from app.modules.shared.schemas.api_response import ApiResponse
from app.modules.stores.repository.store_repository import StoreRepository
from app.modules.products.service.product_service import ProductService

ALLOWED_TYPES = {"promotion", "coupon"}


class DiscountService:

    def __init__(self):
        self.discount_repository = DiscountRepository()
        self.store_repository = StoreRepository()
        self.product_repository = ProductRepository()
        self.product_service = ProductService()

    def _get_store_or_raise(self, session: Session, store_id: int):
        store = self.store_repository.get_by_id(session, store_id)

        if not store:
            raise NotFoundException(
                "No existe una tienda con el identificador indicado."
            )

        return store

    def _get_discount_or_raise(self, session: Session, discount_id: int) -> Discounts:
        discount = self.discount_repository.get_by_id(session, discount_id)

        if not discount:
            raise NotFoundException(
                "No existe un descuento con el identificador indicado."
            )

        return discount

    def _validate_product_for_store(
        self, session: Session, store_id: int, product_id: int | None
    ) -> None:
        if product_id is None:
            return

        product = self.product_repository.get_by_id(session, product_id)

        if not product:
            raise NotFoundException(
                "No existe un producto con el identificador indicado."
            )

        if product.store_id != store_id:
            raise BadRequestException(
                "El producto no pertenece a la tienda indicada."
            )

    def _validate_discount_rules(
        self,
        session: Session,
        store_id: int,
        discount_type: str,
        code: str | None,
        discount_percent: Decimal,
        starts_at,
        ends_at,
        exclude_discount_id: int | None = None,
    ) -> None:
        if discount_type not in ALLOWED_TYPES:
            raise BadRequestException(
                "El tipo debe ser 'promotion' o 'coupon'."
            )

        if discount_percent <= 0 or discount_percent > 100:
            raise BadRequestException(
                "El porcentaje de descuento debe estar entre 0 y 100."
            )

        if discount_type == "coupon" and not code:
            raise BadRequestException(
                "Los cupones requieren un código."
            )

        if starts_at and ends_at and ends_at < starts_at:
            raise BadRequestException(
                "La fecha de fin no puede ser anterior a la fecha de inicio."
            )

        if code:
            existing = self.discount_repository.get_by_code_and_store_id(
                session, store_id, code
            )
            if existing and existing.id != exclude_discount_id:
                raise ConflictException(
                    "Ya existe un descuento con ese código en esta tienda."
                )

    def create(self, session: Session, payload: DiscountCreate):
        self._get_store_or_raise(session, payload.store_id)
        self._validate_product_for_store(
            session, payload.store_id, payload.product_id
        )
        self._validate_discount_rules(
            session,
            payload.store_id,
            payload.type,
            payload.code,
            payload.discount_percent,
            payload.starts_at,
            payload.ends_at,
        )

        new_discount = Discounts(
            store_id=payload.store_id,
            product_id=payload.product_id,
            type=payload.type,
            name=payload.name,
            code=payload.code,
            discount_percent=payload.discount_percent,
            starts_at=payload.starts_at,
            ends_at=payload.ends_at,
            is_active=payload.is_active,
        )

        created = self.discount_repository.create(session, new_discount)

        if created.id is None:
            raise InternalServerException("No fue posible crear el descuento.")

        if payload.product_id is not None:
            product = self.product_repository.get_by_id(session, payload.product_id)

            if product is None:
                raise NotFoundException(
                    "No existe un producto con el identificador indicado."
                )

            discounted_price = calculate_discounted_price(
                product.price,
                payload.discount_percent,
            )

            self.product_service.update(
                session,
                payload.product_id,
                ProductUpdate(
                    price=discounted_price,
                    discount_activate=True,
                ),
            )

        return ApiResponse(
            message="El descuento se creó de manera exitosa.",
            data=DiscountResponse.model_validate(created),
        )

    def get_all(self, session: Session):
        discounts = self.discount_repository.get_all(session)

        return ApiResponse(
            message="Descuentos obtenidos correctamente.",
            data=[DiscountResponse.model_validate(item) for item in discounts],
        )

    def get_by_store_id(self, session: Session, store_id: int):
        self._get_store_or_raise(session, store_id)

        discounts = self.discount_repository.get_by_store_id(session, store_id)

        return ApiResponse(
            message="Descuentos obtenidos correctamente.",
            data=[DiscountResponse.model_validate(item) for item in discounts],
        )

    def get_by_id(self, session: Session, discount_id: int):
        discount = self._get_discount_or_raise(session, discount_id)

        return ApiResponse(
            message="Descuento obtenido correctamente.",
            data=DiscountResponse.model_validate(discount),
        )

    def update(self, session: Session, discount_id: int, payload: DiscountUpdate):
        discount = self._get_discount_or_raise(session, discount_id)

        update_data = payload.model_dump(exclude_unset=True)

        if not update_data:
            raise BadRequestException(
                "No se enviaron datos para actualizar el descuento."
            )

        product_id = update_data.get("product_id", discount.product_id)
        self._validate_product_for_store(session, discount.store_id, product_id)

        discount_type = update_data.get("type", discount.type)
        code = update_data.get("code", discount.code)
        discount_percent = update_data.get(
            "discount_percent", discount.discount_percent
        )
        starts_at = update_data.get("starts_at", discount.starts_at)
        ends_at = update_data.get("ends_at", discount.ends_at)

        self._validate_discount_rules(
            session,
            discount.store_id,
            discount_type,
            code,
            discount_percent,
            starts_at,
            ends_at,
            exclude_discount_id=discount.id,
        )

        for field, value in update_data.items():
            setattr(discount, field, value)

        updated = self.discount_repository.update(session, discount)

        return ApiResponse(
            message="El descuento se actualizó de manera exitosa.",
            data=DiscountResponse.model_validate(updated),
        )

    def delete(self, session: Session, discount_id: int):
        discount = self._get_discount_or_raise(session, discount_id)

        self.discount_repository.delete(session, discount)

        return ApiResponse(
            message="El descuento se eliminó de manera exitosa.",
            data=DiscountResponse.model_validate(discount),
        )
