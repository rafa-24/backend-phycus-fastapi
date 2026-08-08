from sqlmodel import Session, select

from app.modules.orders.models.order_model import OrderItems, Orders


class OrderRepository:
    def create(self, session: Session, order: Orders) -> Orders:
        session.add(order)
        session.commit()
        session.refresh(order)
        return order

    def create_items(
        self, session: Session, items: list[OrderItems]
    ) -> list[OrderItems]:
        for item in items:
            session.add(item)
        session.commit()
        for item in items:
            session.refresh(item)
        return items

    def get_by_id(self, session: Session, order_id: int) -> Orders | None:
        statement = select(Orders).where(Orders.id == order_id)
        return session.exec(statement).first()

    def get_by_identifier(
        self, session: Session, order_identifier: str
    ) -> Orders | None:
        statement = select(Orders).where(
            Orders.order_identifier == order_identifier
        )
        return session.exec(statement).first()

    def get_by_bold_payment_id(
        self, session: Session, payment_id: str
    ) -> Orders | None:
        statement = select(Orders).where(Orders.bold_payment_id == payment_id)
        return session.exec(statement).first()

    def get_by_store_id(self, session: Session, store_id: int) -> list[Orders]:
        statement = (
            select(Orders)
            .where(Orders.store_id == store_id)
            .order_by(Orders.created_at.desc())
        )
        return list(session.exec(statement).all())

    def get_items_by_order_id(
        self, session: Session, order_id: int
    ) -> list[OrderItems]:
        statement = select(OrderItems).where(OrderItems.order_id == order_id)
        return list(session.exec(statement).all())

    def update(self, session: Session, order: Orders) -> Orders:
        session.add(order)
        session.commit()
        session.refresh(order)
        return order
