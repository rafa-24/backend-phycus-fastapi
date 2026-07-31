from sqlmodel import Session

from app.modules.auth.schema.auth_schema import (
    AuthResponse,
    ChangePasswordRequest,
    ChangePasswordResponse,
    LoginRequest,
    PasswordRecoveryRequest,
    PasswordRecoveryResponse,
)
from app.modules.auth.utils.jwt import create_access_token
from app.modules.auth.utils.password import hash_password, verify_password
from app.modules.auth.utils.recovery_code import generate_recovery_code
from app.modules.email.service.email_service import EmailService
from app.modules.shared.schemas.api_response import ApiResponse
from app.modules.shared.exceptions.app_exceptions import (
    BadRequestException,
    NotFoundException,
    UnauthorizedException,
)
from app.modules.users.repository.user_repository import UserRepository
from app.modules.collaborators.repository.collaborator_repository import (
    CollaboratorRepository,
)
from app.modules.stores.repository.store_repository import StoreRepository


class AuthService:

    def __init__(self):
        self.user_repository = UserRepository()
        self.email_service = EmailService()
        self.collaborator_repository = CollaboratorRepository()
        self.store_repository = StoreRepository()

    def login(self, session: Session, credentials: LoginRequest):
        email = credentials.email.strip().lower()
        user = self.user_repository.get_user_by_email(session, email)

        if not user or not verify_password(credentials.password, user.password):
            raise UnauthorizedException("Correo o contraseña incorrectos.")

        access_token = create_access_token(
            {"sub": str(user.id), "email": user.email, "role_id": user.role_id}
        )

        role_name = user.role.name if user.role else None
        store_id = None
        collaborator_role = None
        is_store_owner = False

        owned_store = self.store_repository.get_by_owner_id(session, user.id)
        if owned_store:
            is_store_owner = True
            store_id = owned_store.id

        collaborator = self.collaborator_repository.get_by_user_id(session, user.id)
        if collaborator:
            store_id = collaborator.store_id
            collaborator_role = collaborator.role
            is_store_owner = False

        return ApiResponse(
            message="Inicio de sesión exitoso.",
            data=AuthResponse(
                access_token=access_token,
                user_id=user.id,
                role_id=user.role_id,
                role_name=role_name,
                store_id=store_id,
                collaborator_role=collaborator_role,
                is_store_owner=is_store_owner,
            ),
        )

    def request_password_recovery(
        self, session: Session, payload: PasswordRecoveryRequest
    ):
        user = self.user_repository.get_user_by_email(session, payload.email)

        if not user:
            raise NotFoundException(
                "No existe un usuario registrado con ese correo electrónico."
            )

        recovery_code = generate_recovery_code()

        self.user_repository.update_password_recovery_code(
            session, user, recovery_code
        )

        html = self.email_service.render_template(
            "password_recovery.html",
            {"name": user.first_name, "code": recovery_code},
        )

        self.email_service.send_email(
            to_email=user.email,
            subject="Código de recuperación de contraseña - Phycus",
            html_content=html,
        )

        return ApiResponse(
            message="Se ha enviado un código de recuperación a su correo electrónico.",
            data=PasswordRecoveryResponse(email=user.email),
        )

    def change_password(self, session: Session, payload: ChangePasswordRequest):
        user = self.user_repository.get_user_by_email(session, payload.email)

        if not user:
            raise NotFoundException(
                "No existe un usuario registrado con ese correo electrónico."
            )

        if user.password_recovery_code is None:
            raise BadRequestException(
                "No hay un código de recuperación activo para este usuario."
            )

        if user.password_recovery_code != payload.code:
            raise BadRequestException("El código de verificación es incorrecto.")

        hashed_password = hash_password(payload.password)

        self.user_repository.update_password(session, user, hashed_password)

        return ApiResponse(
            message="Contraseña actualizada de manera exitosa.",
            data=ChangePasswordResponse(email=user.email),
        )