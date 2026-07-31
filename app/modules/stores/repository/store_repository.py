from datetime import UTC, datetime

from sqlmodel import Session, select

from app.modules.stores.models.store_model import Stores


class StoreRepository:

    def create(self, session: Session, store: Stores) -> Stores:
        session.add(store)
        session.commit()
        session.refresh(store)
        return store

    def get_by_id(self, session: Session, store_id: int) -> Stores | None:
        statement = select(Stores).where(Stores.id == store_id)
        return session.exec(statement).first()

    def get_by_owner_id(self, session: Session, owner_id: int) -> Stores | None:
        statement = select(Stores).where(Stores.owner_id == owner_id)
        return session.exec(statement).first()

    def get_all(self, session: Session) -> list[Stores]:
        statement = select(Stores)
        return session.exec(statement).all()

    def update(self, session: Session, store: Stores) -> Stores:
        store.updated_at = datetime.now(UTC)
        session.add(store)
        session.commit()
        session.refresh(store)
        return store
