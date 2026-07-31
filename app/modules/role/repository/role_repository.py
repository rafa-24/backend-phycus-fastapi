from sqlmodel import Session, select

from app.modules.role.model.role_model import Role


class RoleRepository:

    def create(self, session: Session, role: Role) -> Role:
        session.add(role)
        session.commit()
        session.refresh(role)
        return role


    
    def get_all(self, session: Session) -> list[Role]:
        statement = select(Role)
        return session.exec(statement).all()

    def get_by_id(self, session: Session, role_id: int) -> Role:
        statement = select(Role).where(Role.id == role_id)
        return session.exec(statement).first()
    