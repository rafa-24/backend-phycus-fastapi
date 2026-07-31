from sqlmodel import Session

from app.modules.auth.utils.password import hash_password
from app.modules.collaborators.models.collaborator_model import Collaborators
from app.modules.collaborators.repository.collaborator_repository import (
    CollaboratorRepository,
)
from app.modules.collaborators.schema.collaborator_schema import (
    CollaboratorCreate,
    CollaboratorResponse,
    CollaboratorUpdate,
)
from app.modules.email.service.email_service import EmailService
from app.modules.helpers.generate_password import generate_password
from app.modules.shared.exceptions.app_exceptions import (
    BadRequestException,
    ConflictException,
    InternalServerException,
    NotFoundException,
)
from app.modules.shared.schemas.api_response import ApiResponse
from app.modules.stores.repository.store_repository import StoreRepository
from app.modules.users.models.user_model import Users
from app.modules.users.repository.user_repository import UserRepository
from app.modules.users.service.user_service import UserService


class CollaboratorService:

    def __init__(self):
        self.collaborator_repository = CollaboratorRepository()
        self.store_repository = StoreRepository()
        self.email_service = EmailService()
        self.user_service = UserService()
        self.user_repository = UserRepository()

    def _get_store_or_raise(self, session: Session, store_id: int):
        store = self.store_repository.get_by_id(session, store_id)

        if not store:
            raise NotFoundException(
                "No existe una tienda con el identificador indicado."
            )

        return store

    def _get_collaborator_or_raise(
        self, session: Session, collaborator_id: int
    ) -> Collaborators:
        collaborator = self.collaborator_repository.get_by_id(
            session, collaborator_id
        )

        if not collaborator:
            raise NotFoundException(
                "No existe un colaborador con el identificador indicado."
            )

        return collaborator

    def _split_full_name(self, full_name: str) -> tuple[str, str | None]:
        parts = full_name.strip().split(maxsplit=1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else None
        return first_name, last_name

    def create(self, session: Session, payload: CollaboratorCreate):
        store = self._get_store_or_raise(session, payload.store_id)

        if not payload.email or not payload.email.strip():
            raise BadRequestException(
                "El correo es obligatorio para crear el acceso del colaborador."
            )

        email = payload.email.strip().lower()

        if self.user_service.email_exists(session, email):
            raise ConflictException("Este correo esta asociada a otra cuenta.")

        password_collaborator = generate_password()
        first_name, last_name = self._split_full_name(payload.full_name)

        new_user = Users(
            email=email,
            password=hash_password(password_collaborator),
            first_name=first_name,
            last_name=last_name,
            role_id=2,
        )
        created_user = self.user_repository.create(session, new_user)

        if created_user.id is None:
            raise InternalServerException("No fue posible crear el usuario del colaborador.")

        new_collaborator = Collaborators(
            store_id=payload.store_id,
            user_id=created_user.id,
            full_name=payload.full_name.strip(),
            email=email,
            role=payload.role,
            is_active=payload.is_active,
        )

        created = self.collaborator_repository.create(session, new_collaborator)

        if created.id is None:
            raise InternalServerException("No fue posible crear el colaborador.")

        html = self.email_service.render_template(
            "invitation_collaborator.html",
            {
                "name": payload.full_name,
                "storeName": store.name,
                "email": email,
                "password": password_collaborator,
                "loginUrl": "",
            },
        )

        self.email_service.send_email(
            to_email=email,
            subject="Tu acceso a Phycus ha sido creado",
            html_content=html,
        )

        return ApiResponse(
            message="El colaborador se creó de manera exitosa.",
            data=CollaboratorResponse.model_validate(created),
        )

    def get_all(self, session: Session):
        collaborators = self.collaborator_repository.get_all(session)

        return ApiResponse(
            message="Colaboradores obtenidos correctamente.",
            data=[
                CollaboratorResponse.model_validate(item) for item in collaborators
            ],
        )

    def get_by_store_id(self, session: Session, store_id: int):
        self._get_store_or_raise(session, store_id)

        collaborators = self.collaborator_repository.get_by_store_id(
            session, store_id
        )

        return ApiResponse(
            message="Colaboradores obtenidos correctamente.",
            data=[
                CollaboratorResponse.model_validate(item) for item in collaborators
            ],
        )

    def get_by_id(self, session: Session, collaborator_id: int):
        collaborator = self._get_collaborator_or_raise(session, collaborator_id)

        return ApiResponse(
            message="Colaborador obtenido correctamente.",
            data=CollaboratorResponse.model_validate(collaborator),
        )

    def update(
        self, session: Session, collaborator_id: int, payload: CollaboratorUpdate
    ):
        collaborator = self._get_collaborator_or_raise(session, collaborator_id)

        update_data = payload.model_dump(exclude_unset=True)

        if not update_data:
            raise BadRequestException(
                "No se enviaron datos para actualizar el colaborador."
            )

        for field, value in update_data.items():
            setattr(collaborator, field, value)

        updated = self.collaborator_repository.update(session, collaborator)

        return ApiResponse(
            message="El colaborador se actualizó de manera exitosa.",
            data=CollaboratorResponse.model_validate(updated),
        )

    def delete(self, session: Session, collaborator_id: int):
        collaborator = self._get_collaborator_or_raise(session, collaborator_id)

        # eliminar de la tabla users
        deleted_user = self.user_service.delete_user_by_email(session, collaborator.email)

        print(f"delete_user ${deleted_user}")


        self.collaborator_repository.delete(session, collaborator)

        return ApiResponse(
            message="El colaborador se eliminó de manera exitosa.",
            data=CollaboratorResponse.model_validate(collaborator),
        )

    def get_by_user_id(self, session: Session, user_id: int):
        collaborator = self.collaborator_repository.get_by_user_id(session, user_id)

        if not collaborator:
            raise NotFoundException(
                "No existe un colaborador asociado a este usuario."
            )

        return ApiResponse(
            message="Colaborador obtenido correctamente.",
            data=CollaboratorResponse.model_validate(collaborator),
        )
