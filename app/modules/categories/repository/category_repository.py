from sqlmodel import Session, select

from app.modules.categories.models.category_model import Categories


class CategoryRepository:

    def create(self, session: Session, category: Categories) -> Categories:
        session.add(category)
        session.commit()
        session.refresh(category)
        return category

    def get_by_id(self, session: Session, category_id: int) -> Categories | None:
        statement = select(Categories).where(Categories.id == category_id)
        return session.exec(statement).first()

    def get_all(self, session: Session) -> list[Categories]:
        statement = select(Categories)
        return session.exec(statement).all()

    def get_by_store_id(self, session: Session, store_id: int) -> list[Categories]:
        statement = select(Categories).where(Categories.store_id == store_id)
        return session.exec(statement).all()

    def get_by_name_and_store_id(
        self, session: Session, store_id: int, name: str
    ) -> Categories | None:
        statement = select(Categories).where(
            Categories.store_id == store_id,
            Categories.name == name,
        )
        return session.exec(statement).first()

    def update(self, session: Session, category: Categories) -> Categories:
        session.add(category)
        session.commit()
        session.refresh(category)
        return category

    def delete(self, session: Session, category: Categories) -> None:
        session.delete(category)
        session.commit()
