from sqlmodel import Session, select

from app.modules.discounts.models.discount_model import Discounts


class DiscountRepository:

    def create(self, session: Session, discount: Discounts) -> Discounts:
        session.add(discount)
        session.commit()
        session.refresh(discount)
        return discount

    def get_by_id(self, session: Session, discount_id: int) -> Discounts | None:
        statement = select(Discounts).where(Discounts.id == discount_id)
        return session.exec(statement).first()

    def get_all(self, session: Session) -> list[Discounts]:
        statement = select(Discounts)
        return session.exec(statement).all()

    def get_by_store_id(self, session: Session, store_id: int) -> list[Discounts]:
        statement = select(Discounts).where(Discounts.store_id == store_id)
        return session.exec(statement).all()

    def get_by_code_and_store_id(
        self, session: Session, store_id: int, code: str
    ) -> Discounts | None:
        statement = select(Discounts).where(
            Discounts.store_id == store_id,
            Discounts.code == code,
        )
        return session.exec(statement).first()

    def update(self, session: Session, discount: Discounts) -> Discounts:
        session.add(discount)
        session.commit()
        session.refresh(discount)
        return discount

    def delete(self, session: Session, discount: Discounts) -> None:
        session.delete(discount)
        session.commit()
