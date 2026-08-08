from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.database.session import get_session
from app.modules.integrations.siigo.schema.sigo_details_schema import (
    SigoDetailCreate,
    SigoDetailUpdate,
)
from app.modules.integrations.siigo.service.sigo_detail_service import SiigoService

siigo = APIRouter(
    prefix="/siigo",
    tags=["siigo"],
)

siigo_service = SiigoService()


@siigo.post("", status_code=status.HTTP_201_CREATED)
async def create(
    payload: SigoDetailCreate,
    session: Session = Depends(get_session),
):
    """Valida credenciales contra Siigo y guarda/actualiza la conexión."""
    return await siigo_service.create_connection_sigo(session, payload)


@siigo.get("/store/{store_id}", status_code=status.HTTP_200_OK)
def list_by_store(store_id: int, session: Session = Depends(get_session)):
    return siigo_service.list_connections(session, store_id)


@siigo.get("/store/{store_id}/current", status_code=status.HTTP_200_OK)
def get_current(store_id: int, session: Session = Depends(get_session)):
    return siigo_service.get_connection(session, store_id)


@siigo.post(
    "/store/{store_id}/sync-products",
    status_code=status.HTTP_200_OK,
)
async def sync_products(store_id: int, session: Session = Depends(get_session)):
    """
    Trae productos/inventario de Siigo y los crea o actualiza en Phycus.
    Requiere conexión Siigo activa.
    """
    return await siigo_service.sync_products(session, store_id)


@siigo.patch(
    "/store/{store_id}/{siigo_detail_id}",
    status_code=status.HTTP_200_OK,
)
async def update(
    store_id: int,
    siigo_detail_id: int,
    payload: SigoDetailUpdate,
    session: Session = Depends(get_session),
):
    return await siigo_service.update_connection(
        session, store_id, siigo_detail_id, payload
    )


@siigo.delete(
    "/store/{store_id}/{siigo_detail_id}",
    status_code=status.HTTP_200_OK,
)
def delete(
    store_id: int,
    siigo_detail_id: int,
    session: Session = Depends(get_session),
):
    return siigo_service.delete_connection(session, store_id, siigo_detail_id)
