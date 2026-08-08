from sqlmodel import Session, select

from app.modules.integrations.payments.bold.models.paymentDetails_models import PaymentDetail


class BoldRepository:

    def create(self, session: Session, payment_detail: PaymentDetail) -> PaymentDetail:
        session.add(payment_detail)
        session.commit()
        session.refresh(payment_detail)
        return payment_detail

    def get_by_id(
        self, session: Session, payment_detail_id: int
    ) -> PaymentDetail | None:
        statement = select(PaymentDetail).where(PaymentDetail.id == payment_detail_id)
        return session.exec(statement).first()

    def get_all(self, session: Session, store_id: int) -> list[PaymentDetail]:
        statement = select(PaymentDetail).where(PaymentDetail.store_id == store_id)
        return list(session.exec(statement).all())

    def get_all_configs(self, session: Session) -> list[PaymentDetail]:
        statement = select(PaymentDetail)
        return list(session.exec(statement).all())

    def update(self, session: Session, payment_detail: PaymentDetail) -> PaymentDetail:
        session.add(payment_detail)
        session.commit()
        session.refresh(payment_detail)
        return payment_detail

    def delete(self, session: Session, payment_detail: PaymentDetail) -> None:
        session.delete(payment_detail)
        session.commit()
