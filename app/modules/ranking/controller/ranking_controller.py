from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.database.session import get_session
from app.modules.ranking.service.ranking_service import RankingService

ranking = APIRouter(
    prefix="/ranking",
    tags=["ranking"],
)

# inicializacion del servicio
ranking_service = RankingService()


@ranking.post('/{product_id}', status_code=status.HTTP_201_CREATED)
async def create(product_id: int, session: Session = Depends(get_session)):
    return await ranking_service.create(session, product_id)


@ranking.put('/{product_id}', status_code=status.HTTP_200_OK)
async def update(product_id: int, session: Session = Depends(get_session)):
    return await ranking_service.update(session, product_id)


@ranking.get('', status_code=status.HTTP_200_OK)
def get(session: Session = Depends(get_session)):
    return ranking_service.get_ranking(session)


@ranking.get('/{product_id}', status_code=status.HTTP_200_OK)
def get_ranking_images_by_product(product_id: int, session: Session = Depends(get_session)):
    return ranking_service.get_images_by_id(session, product_id)


@ranking.delete('/{product_id}', status_code=status.HTTP_200_OK)
def delete_ranking_by_product(product_id: int, session: Session = Depends(get_session)):
    return ranking_service.delete_by_product_id(session, product_id)


