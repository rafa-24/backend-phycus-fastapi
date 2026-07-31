from sqlmodel import Session, select

from app.modules.ranking.models.ranking_products import Ranking


class RankingRepository:

    def create(self, session: Session, ranking: Ranking) -> Ranking:
        session.add(ranking)
        session.commit()
        session.refresh(ranking)
        return ranking

    def get(self, session: Session) -> list[Ranking]:
        statement = select(Ranking)
        return session.exec(statement).all()

    def get_by_product_id(
        self, session: Session, product_id: int
    ) -> list[Ranking]:
        statement = select(Ranking).where(Ranking.product_id == product_id)
        return session.exec(statement).all()

    def delete_by_product_id(
        self, session: Session, product_id: int
    ) -> list[Ranking]:
        rankings = self.get_by_product_id(session, product_id)

        for ranking in rankings:
            session.delete(ranking)

        if rankings:
            session.commit()

        return rankings
