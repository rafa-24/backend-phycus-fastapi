from sqlmodel import Session

from app.modules.role.model.role_model import Role
from app.modules.role.schema.role_schema import RoleCreate
from app.modules.role.repository.role_repository import RoleRepository

from app.modules.shared.exceptions.app_exceptions import InternalServerException
from app.modules.shared.schemas.api_response import ApiResponse

class RoleService:

    def __init__(self):
        self.role_repository = RoleRepository()

    def create(self, session: Session, payload: RoleCreate):
        role = Role(
            name = payload.name
        )

        created_role = self.role_repository.create(session, role)

        if (created_role.id is None):
            raise InternalServerException("No fue posible crear el colaborador.")

        return ApiResponse(
            message= 'Role creado con exito',
            data=  created_role
        )   

    def get_all(self, session: Session):    
        return self.role_repository.get_all(session)

    def get_by_id(self, session: Session, role_id: int):
        return self.role_repository.get_by_id(session, role_id)

