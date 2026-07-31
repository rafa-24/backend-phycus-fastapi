from sqlmodel import Session

from app.modules.categories.models.category_model import Categories
from app.modules.categories.repository.category_repository import CategoryRepository
from app.modules.categories.schema.category_schema import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
)
from app.modules.products.repository.product_repository import ProductRepository
from app.modules.shared.exceptions.app_exceptions import (
    BadRequestException,
    InternalServerException,
    NotFoundException,
)
from app.modules.shared.schemas.api_response import ApiResponse
from app.modules.stores.repository.store_repository import StoreRepository


class CategoryService:

    def __init__(self):
        self.category_repository = CategoryRepository()
        self.store_repository = StoreRepository()
        self.product_repository = ProductRepository()

    def _get_store_or_raise(self, session: Session, store_id: int):
        store = self.store_repository.get_by_id(session, store_id)

        if not store:
            raise NotFoundException("No existe una tienda con el identificador indicado.")

        return store

    def _get_category_or_raise(self, session: Session, category_id: int) -> Categories:
        category = self.category_repository.get_by_id(session, category_id)

        if not category:
            raise NotFoundException(
                "No existe una categoría con el identificador indicado."
            )

        return category

    def create(self, session: Session, payload: CategoryCreate):
        self._get_store_or_raise(session, payload.store_id)

        new_category = Categories(
            store_id=payload.store_id,
            name=payload.name,
        )

        created_category = self.category_repository.create(session, new_category)

        if created_category.id is None:
            raise InternalServerException("No fue posible crear la categoría.")

        return ApiResponse(
            message="La categoría se creó de manera exitosa.",
            data=CategoryResponse.model_validate(created_category),
        )

    def get_all(self, session: Session):
        categories = self.category_repository.get_all(session)

        return ApiResponse(
            message="Categorías obtenidas correctamente.",
            data=[
                CategoryResponse.model_validate(category) for category in categories
            ],
        )

    def get_by_store_id(self, session: Session, store_id: int):
        self._get_store_or_raise(session, store_id)

        categories = self.category_repository.get_by_store_id(session, store_id)

        return ApiResponse(
            message="Categorías obtenidas correctamente.",
            data=[
                CategoryResponse.model_validate(category) for category in categories
            ],
        )

    def get_by_id(self, session: Session, category_id: int):
        category = self._get_category_or_raise(session, category_id)

        return ApiResponse(
            message="Categoría obtenida correctamente.",
            data=CategoryResponse.model_validate(category),
        )

    def update(self, session: Session, category_id: int, payload: CategoryUpdate):
        category = self._get_category_or_raise(session, category_id)

        update_data = payload.model_dump(exclude_unset=True)

        if not update_data:
            raise BadRequestException(
                "No se enviaron datos para actualizar la categoría."
            )

        for field, value in update_data.items():
            setattr(category, field, value)

        updated_category = self.category_repository.update(session, category)

        return ApiResponse(
            message="La categoría se actualizó de manera exitosa.",
            data=CategoryResponse.model_validate(updated_category),
        )

    def delete(self, session: Session, category_id: int):
        category = self._get_category_or_raise(session, category_id)

        products = self.product_repository.get_by_category_id(session, category_id)

        for product in products:
            product.category_id = None
            self.product_repository.update(session, product)

        self.category_repository.delete(session, category)

        return ApiResponse(
            message="La categoría se eliminó de manera exitosa.",
            data=CategoryResponse.model_validate(category),
        )
