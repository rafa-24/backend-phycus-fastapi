from sqlmodel import Session, select

from app.modules.products.models.product_model import Products


class ProductRepository:

    def create(self, session: Session, product: Products) -> Products:
        session.add(product)
        session.commit()
        session.refresh(product)
        return product

    def get_by_id(self, session: Session, product_id: int) -> Products | None:
        statement = select(Products).where(Products.id == product_id)
        return session.exec(statement).first()

    def get_all(self, session: Session) -> list[Products]:
        statement = select(Products)
        return session.exec(statement).all()

    def get_by_store_id(self, session: Session, store_id: int) -> list[Products]:
        statement = select(Products).where(Products.store_id == store_id)
        return session.exec(statement).all()

    def get_by_siigo_id(
        self, session: Session, store_id: int, siigo_id: str
    ) -> Products | None:
        statement = (
            select(Products)
            .where(Products.store_id == store_id)
            .where(Products.siigo_id == siigo_id)
        )
        return session.exec(statement).first()

    def get_by_siigo_code(
        self, session: Session, store_id: int, siigo_code: str
    ) -> Products | None:
        statement = (
            select(Products)
            .where(Products.store_id == store_id)
            .where(Products.siigo_code == siigo_code)
        )
        return session.exec(statement).first()

    def get_by_category_id(
        self, session: Session, category_id: int
    ) -> list[Products]:
        statement = select(Products).where(Products.category_id == category_id)
        return session.exec(statement).all()

    def update(self, session: Session, product: Products) -> Products:
        session.add(product)
        session.commit()
        session.refresh(product)
        return product

    def delete(self, session: Session, product: Products) -> None:
        session.delete(product)
        session.commit()
