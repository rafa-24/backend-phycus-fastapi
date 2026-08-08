from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.database.session import get_session
from app.modules.analytics.service.analytics_service import AnalyticsService

analytics = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
)

analytics_service = AnalyticsService()


@analytics.get("/store/{store_id}/dashboard", status_code=status.HTTP_200_OK)
def get_dashboard(store_id: int, session: Session = Depends(get_session)):
    """
    Dashboard de analítica de negocio:
    KPIs semanales, ingresos diarios, crecimiento mensual,
    rotación de inventario y alertas de stock.
    """
    return analytics_service.get_dashboard(session, store_id)
