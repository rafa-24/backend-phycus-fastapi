from sqlmodel import Session, select

from app.modules.collaborators.models.collaborator_model import Collaborators


class CollaboratorRepository:

    def create(self, session: Session, collaborator: Collaborators) -> Collaborators:
        session.add(collaborator)
        session.commit()
        session.refresh(collaborator)
        return collaborator

    def get_by_id(
        self, session: Session, collaborator_id: int
    ) -> Collaborators | None:
        statement = select(Collaborators).where(Collaborators.id == collaborator_id)
        return session.exec(statement).first()

    def get_all(self, session: Session) -> list[Collaborators]:
        statement = select(Collaborators)
        return session.exec(statement).all()

    def get_by_store_id(
        self, session: Session, store_id: int
    ) -> list[Collaborators]:
        statement = select(Collaborators).where(Collaborators.store_id == store_id)
        return session.exec(statement).all()

    def get_by_user_id(
        self, session: Session, user_id: int
    ) -> Collaborators | None:
        statement = select(Collaborators).where(Collaborators.user_id == user_id)
        return session.exec(statement).first()

    def get_by_email(self, session: Session, email: str) -> Collaborators | None:
        statement = select(Collaborators).where(Collaborators.email == email)
        return session.exec(statement).first()

    def update(self, session: Session, collaborator: Collaborators) -> Collaborators:
        session.add(collaborator)
        session.commit()
        session.refresh(collaborator)
        return collaborator

    def delete(self, session: Session, collaborator: Collaborators) -> None:
        session.delete(collaborator)
        session.commit()
