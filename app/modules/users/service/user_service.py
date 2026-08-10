from sqlmodel import Session

from app.modules.users.schema.user_schema import UserCreate, UserResponse, RoleResponse
from app.modules.users.models.user_model import Users
from app.modules.users.repository.user_repository import UserRepository
from app.modules.auth.utils.password import hash_password
from app.modules.role.service.role_service import RoleService

from app.modules.shared.schemas.api_response import ApiResponse
from app.modules.email.service.email_service import EmailService
from app.modules.shared.exceptions.app_exceptions import (
    ConflictException,
    InternalServerException,
    NotFoundException,
)

class UserService:

    def __init__(self):
        self.user_repository = UserRepository()
        self.email_service = EmailService()
        self.role_service = RoleService()


    def create(self, session: Session, user: UserCreate):

        email = user.email.strip().lower()
        existing_user = self.user_repository.get_user_by_email(session, email)

        if existing_user:
            raise ConflictException("El correo ya esta registrado.")
        
        # Instanciar nuevo usuario
        new_user = Users(
            email=email,
            password=hash_password(user.password),
            first_name=user.first_name,
            last_name=user.last_name,
            cellphone=user.cellphone,
            role_id=1,
        )

        # Guardar en la db
        created_user = self.user_repository.create(session, new_user)

        print(f'usuario creados: {created_user}')

        # verificar si el usuario se creo
        if created_user.id is None:
            raise InternalServerException("No fue posible crear usuario")

        # Crear una tienda y asociarla a este usuario
        
        # enviar email
        html = self.email_service.render_template(
            "welcome.html",
            {"name": created_user.first_name}
        )

        self.email_service.send_email(
            to_email= created_user.email,
            subject= "Bienvenido a phycus",
            html_content= html
        )

        return ApiResponse(
            message= "Su registro se completo de manera exitosa.",
            data= self._to_user_response(created_user)
        )

    def _to_user_response(self, user: Users) -> UserResponse:
        role = None
        if user.role:
            role = RoleResponse(id=user.role.id, name=user.role.name)

        return UserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            cellphone=user.cellphone,
            role_id=user.role_id,
            role=role,
        )

    def get_all(self, session: Session):
        users = self.user_repository.get_all(session)

        return ApiResponse(
            message="Usuarios obtenidos correctamente.",
            data=[self._to_user_response(user) for user in users],
        )

    def get_by_id(self, session: Session, user_id: int):
        user = self.user_repository.get_user_by_id(session, user_id)

        if not user:
            raise NotFoundException(
                "No existe un usuario con el identificador indicado."
            )

        return ApiResponse(
            message="Usuario obtenido correctamente.",
            data=self._to_user_response(user),
        )

    def email_exists(self, session: Session, email: str) -> bool:
        user = self.user_repository.get_user_by_email(session, email.strip().lower())
        return user is not None

    def delete_user_by_email(self, session: Session, email: str):
        user = self.user_repository.get_user_by_email(session, email)

        if(user):
            self.user_repository.delete(session, user)
            return ApiResponse(message= f'Usuario eliminado')

        raise NotFoundException("No existe un usuario con el identificador indicado.")