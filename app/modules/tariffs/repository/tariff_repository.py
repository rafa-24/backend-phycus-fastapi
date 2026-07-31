from sqlmodel import Session, select

from app.modules.tariffs.models.tariff_model import Tariffs


class TariffRepository:
    def create(self, session: Session, tariff: Tariffs) -> Tariffs:
        session.add(tariff)
        session.commit()
        session.refresh(tariff)
        return tariff

    def get_by_id(self, session: Session, tariff_id: int) -> Tariffs | None:
        statement = select(Tariffs).where(Tariffs.id == tariff_id)
        return session.exec(statement).first()

    def get_by_store_id(self, session: Session, store_id: int) -> list[Tariffs]:
        statement = select(Tariffs).where(Tariffs.store_id == store_id)
        return list(session.exec(statement).all())

    def get_by_store_and_barrio(
        self,
        session: Session,
        store_id: int,
        barrio: str,
        localidad: str,
    ) -> Tariffs | None:
        statement = select(Tariffs).where(
            Tariffs.store_id == store_id,
            Tariffs.barrio == barrio,
            Tariffs.localidad == localidad,
        )
        return session.exec(statement).first()

    def update(self, session: Session, tariff: Tariffs) -> Tariffs:
        session.add(tariff)
        session.commit()
        session.refresh(tariff)
        return tariff

    def delete(self, session: Session, tariff: Tariffs) -> None:
        session.delete(tariff)
        session.commit()

    def create_many(self, session: Session, tariffs: list[Tariffs]) -> list[Tariffs]:
        session.add_all(tariffs)
        session.commit()
        for tariff in tariffs:
            session.refresh(tariff)
        return tariffs
