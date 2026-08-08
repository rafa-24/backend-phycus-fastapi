from sqlmodel import Session, select

from app.modules.integrations.siigo.models.sigo_details_model import SiigoDetail


class SiigoRepository:
    def create(self, session: Session, sigo_detail: SiigoDetail) -> SiigoDetail:
        session.add(sigo_detail)
        session.commit()
        session.refresh(sigo_detail)
        return sigo_detail

    def get_by_id(self, session: Session, siigo_detail_id: int) -> SiigoDetail | None:
        statement = select(SiigoDetail).where(SiigoDetail.id == siigo_detail_id)
        return session.exec(statement).first()

    def get_all(self, session: Session, store_id: int) -> list[SiigoDetail]:
        statement = select(SiigoDetail).where(SiigoDetail.store_id == store_id)
        return list(session.exec(statement).all())

    def get_latest_by_store(
        self, session: Session, store_id: int
    ) -> SiigoDetail | None:
        statement = (
            select(SiigoDetail)
            .where(SiigoDetail.store_id == store_id)
            .order_by(SiigoDetail.created_at.desc())
        )
        return session.exec(statement).first()

    def update(self, session: Session, sigo_detail: SiigoDetail) -> SiigoDetail:
        session.add(sigo_detail)
        session.commit()
        session.refresh(sigo_detail)
        return sigo_detail

    def delete(self, session: Session, sigo_detail: SiigoDetail) -> None:
        session.delete(sigo_detail)
        session.commit()
