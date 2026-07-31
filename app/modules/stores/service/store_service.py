from sqlmodel import Session

from app.modules.shared.exceptions.app_exceptions import (
    BadRequestException,
    ConflictException,
    InternalServerException,
    NotFoundException,
)
from app.modules.shared.schemas.api_response import ApiResponse
from app.modules.stores.models.store_model import Stores
from app.modules.stores.repository.store_repository import StoreRepository
from app.modules.stores.schema.store_schema import (
    StoreCreate,
    StoreResponse,
    StoreUpdate,
)
from app.modules.users.repository.user_repository import UserRepository

ALLOWED_STATUSES = {"draft", "published"}


class StoreService:

    def __init__(self):
        self.store_repository = StoreRepository()
        self.user_repository = UserRepository()

    def create(self, session: Session, payload: StoreCreate):
        owner = self.user_repository.get_user_by_id(session, payload.owner_id)

        if not owner:
            raise NotFoundException("No existe un usuario con el identificador indicado.")

        existing_store = self.store_repository.get_by_owner_id(
            session, payload.owner_id
        )

        if existing_store:
            raise ConflictException("Este usuario ya tiene una tienda registrada.")

        new_store = Stores(
            owner_id=payload.owner_id,
            name=payload.name,
            description=payload.description,
            logo_url=payload.logo_url,
            city=(payload.city or "Barranquilla").strip() or "Barranquilla",
            status="draft",
        )

        created_store = self.store_repository.create(session, new_store)

        if created_store.id is None:
            raise InternalServerException("No fue posible crear la tienda.")

        return ApiResponse(
            message="La tienda se creó de manera exitosa.",
            data=StoreResponse.model_validate(created_store),
        )

    def get_all(self, session: Session):
        stores = self.store_repository.get_all(session)

        return ApiResponse(
            message="Tiendas obtenidas correctamente.",
            data=[StoreResponse.model_validate(store) for store in stores],
        )

    def get_by_id(self, session: Session, store_id: int):
        store = self.store_repository.get_by_id(session, store_id)

        if not store:
            raise NotFoundException("No existe una tienda con el identificador indicado.")

        return ApiResponse(
            message="Tienda obtenida correctamente.",
            data=StoreResponse.model_validate(store),
        )

    def get_by_owner_id(self, session: Session, owner_id: int):
        owner = self.user_repository.get_user_by_id(session, owner_id)

        if not owner:
            raise NotFoundException("No existe un usuario con el identificador indicado.")

        store = self.store_repository.get_by_owner_id(session, owner_id)

        if not store:
            raise NotFoundException("Este usuario no tiene una tienda registrada.")

        return ApiResponse(
            message="Tienda obtenida correctamente.",
            data=StoreResponse.model_validate(store),
        )

    def update(self, session: Session, store_id: int, payload: StoreUpdate):
        store = self.store_repository.get_by_id(session, store_id)

        if not store:
            raise NotFoundException("No existe una tienda con el identificador indicado.")

        update_data = payload.model_dump(exclude_unset=True)

        if not update_data:
            raise BadRequestException("No se enviaron datos para actualizar la tienda.")

        if "status" in update_data and update_data["status"] not in ALLOWED_STATUSES:
            raise BadRequestException("El estado debe ser 'draft' o 'published'.")

        for field, value in update_data.items():
            setattr(store, field, value)

        updated_store = self.store_repository.update(session, store)

        return ApiResponse(
            message="La tienda se actualizó de manera exitosa.",
            data=StoreResponse.model_validate(updated_store),
        )
