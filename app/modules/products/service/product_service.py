from sqlmodel import Session

from app.modules.categories.models.category_model import Categories
from app.modules.categories.repository.category_repository import CategoryRepository
from app.modules.products.models.product_model import Products
from app.modules.products.repository.product_repository import ProductRepository
from app.modules.ranking.repository.ranking_repository import RankingRepository
from app.modules.products.schema.product_schema import (
    ProductCreate,
    ProductImportResponse,
    ProductImportSkippedRow,
    ProductResponse,
    ProductUpdate,
)
from app.modules.products.utils.excel import (
    create_products_workbook,
    parse_products_workbook,
)
from app.modules.shared.exceptions.app_exceptions import (
    BadRequestException,
    InternalServerException,
    NotFoundException,
)
from app.modules.shared.schemas.api_response import ApiResponse
from app.modules.stores.repository.store_repository import StoreRepository


class ProductService:

    def __init__(self):
        self.product_repository = ProductRepository()
        self.store_repository = StoreRepository()
        self.category_repository = CategoryRepository()
        self.ranking_repository = RankingRepository()

    def _get_store_or_raise(self, session: Session, store_id: int):
        store = self.store_repository.get_by_id(session, store_id)

        if not store:
            raise NotFoundException("No existe una tienda con el identificador indicado.")

        return store

    def _get_product_or_raise(self, session: Session, product_id: int) -> Products:
        product = self.product_repository.get_by_id(session, product_id)

        if not product:
            raise NotFoundException("No existe un producto con el identificador indicado.")

        return product

    def _validate_category_for_store(
        self, session: Session, store_id: int, category_id: int | None
    ) -> None:
        if category_id is None:
            return

        category = self.category_repository.get_by_id(session, category_id)

        if not category:
            raise NotFoundException(
                "No existe una categoría con el identificador indicado."
            )

        if category.store_id != store_id:
            raise BadRequestException(
                "La categoría no pertenece a la tienda indicada."
            )

    def _get_or_create_category(
        self, session: Session, store_id: int, category_name: str
    ) -> tuple[Categories, bool]:
        category = self.category_repository.get_by_name_and_store_id(
            session, store_id, category_name
        )

        if category:
            return category, False

        created_category = self.category_repository.create(
            session,
            Categories(store_id=store_id, name=category_name),
        )

        return created_category, True

    def create(self, session: Session, payload: ProductCreate):
        self._get_store_or_raise(session, payload.store_id)
        self._validate_category_for_store(
            session, payload.store_id, payload.category_id
        )

        if payload.price <= 0:
            raise BadRequestException("El precio debe ser mayor a cero.")

        new_product = Products(
            store_id=payload.store_id,
            category_id=payload.category_id,
            name=payload.name,
            description=payload.description,
            price=payload.price,
            image_url=payload.image_url,
            is_active=payload.is_active,
            stock=payload.stock,
            discount_activate=payload.discount_activate,
            siigo_id=payload.siigo_id,
            siigo_code=payload.siigo_code,
            ean=payload.ean,
        )

        created_product = self.product_repository.create(session, new_product)

        if created_product.id is None:
            raise InternalServerException("No fue posible crear el producto.")

        return ApiResponse(
            message="El producto se creó de manera exitosa.",
            data=ProductResponse.model_validate(created_product),
        )

    def get_all(self, session: Session):
        products = self.product_repository.get_all(session)

        return ApiResponse(
            message=f"el total de productos es {len(products)}",
            data=[ProductResponse.model_validate(product) for product in products],
        )

    def get_by_store_id(self, session: Session, store_id: int):
        self._get_store_or_raise(session, store_id)

        products = self.product_repository.get_by_store_id(session, store_id)

        return ApiResponse(
            message="Productos obtenidos correctamente.",
            data=[ProductResponse.model_validate(product) for product in products],
        )

    def get_by_category_id(self, session: Session, category_id: int):
        category = self.category_repository.get_by_id(session, category_id)

        if not category:
            raise NotFoundException(
                "No existe una categoría con el identificador indicado."
            )

        products = self.product_repository.get_by_category_id(session, category_id)

        return ApiResponse(
            message="Productos obtenidos correctamente.",
            data=[ProductResponse.model_validate(product) for product in products],
        )

    def get_by_id(self, session: Session, product_id: int):
        product = self._get_product_or_raise(session, product_id)

        return ApiResponse(
            message="Producto obtenido correctamente.",
            data=ProductResponse.model_validate(product),
        )

    def update(self, session: Session, product_id: int, payload: ProductUpdate):
        product = self._get_product_or_raise(session, product_id)

        update_data = payload.model_dump(exclude_unset=True)

        if not update_data:
            raise BadRequestException(
                "No se enviaron datos para actualizar el producto."
            )

        category_id = update_data.get("category_id", product.category_id)
        self._validate_category_for_store(session, product.store_id, category_id)

        if "price" in update_data and update_data["price"] <= 0:
            raise BadRequestException("El precio debe ser mayor a cero.")

        for field, value in update_data.items():
            setattr(product, field, value)

        updated_product = self.product_repository.update(session, product)

        return ApiResponse(
            message="El producto se actualizó de manera exitosa.",
            data=ProductResponse.model_validate(updated_product),
        )

    def delete(self, session: Session, product_id: int):
        product = self._get_product_or_raise(session, product_id)
        try:
            # llamada al repositorio para eliminar descuentos, ordenes y rankings asociados al producto
            self.product_repository.delete(session, product)
            session.commit()
        except Exception as e:
            session.rollback()
            raise InternalServerException(f"No fue posible eliminar el producto: {str(e)}")
        
        return ApiResponse(
            message="El producto se eliminó de manera exitosa.", 
            data=ProductResponse.model_validate(product)
        )

    def export_products_excel(self, session: Session, store_id: int):
        self._get_store_or_raise(session, store_id)

        products = self.product_repository.get_by_store_id(session, store_id)
        rows = []

        for product in products:
            category_name = ""

            if product.category_id:
                category = self.category_repository.get_by_id(
                    session, product.category_id
                )
                if category:
                    category_name = category.name

            rows.append(
                {
                    "category_name": category_name,
                    "name": product.name,
                    "description": product.description,
                    "price": product.price,
                    "image_url": product.image_url,
                    "is_active": product.is_active,
                }
            )

        return create_products_workbook(rows)

    def import_products_excel(
        self, session: Session, store_id: int, file_content: bytes
    ):
        self._get_store_or_raise(session, store_id)

        try:
            parsed_result = parse_products_workbook(file_content)
        except ValueError as exc:
            raise BadRequestException(str(exc)) from exc

        parsed_rows = parsed_result["valid_rows"]
        skipped_rows = parsed_result["skipped_rows"]

        created_products = []
        categories_created = 0

        for row in parsed_rows:
            category, was_created = self._get_or_create_category(
                session, store_id, row["category_name"]
            )

            if was_created:
                categories_created += 1

            product = Products(
                store_id=store_id,
                category_id=category.id,
                name=row["name"],
                description=row["description"],
                price=row["price"],
                image_url=row["image_url"],
                is_active=row["is_active"],
            )

            created_product = self.product_repository.create(session, product)

            if created_product.id is None:
                raise InternalServerException(
                    f"No fue posible crear el producto de la fila {row['row_number']}."
                )

            created_products.append(created_product)

        message = "Productos importados de manera exitosa."

        if skipped_rows:
            message = (
                "Importación completada con advertencias. "
                f"Se omitieron {len(skipped_rows)} filas con errores."
            )

        return ApiResponse(
            message=message,
            data=ProductImportResponse(
                products_created=len(created_products),
                categories_created=categories_created,
                rows_skipped=len(skipped_rows),
                skipped_rows=[
                    ProductImportSkippedRow.model_validate(row)
                    for row in skipped_rows
                ],
                products=[
                    ProductResponse.model_validate(product)
                    for product in created_products
                ],
            ),
        )
