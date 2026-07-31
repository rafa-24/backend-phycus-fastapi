from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from app.database.session import get_session
from app.modules.shared.exceptions.app_exceptions import BadRequestException
from app.modules.tariffs.schema.tariff_schema import TariffCreate, TariffUpdate
from app.modules.tariffs.service.tariff_service import TariffService

tariff = APIRouter(
    prefix="/tariff",
    tags=["tariff"],
)

tariff_service = TariffService()


@tariff.post("", status_code=status.HTTP_201_CREATED)
def create(payload: TariffCreate, session: Session = Depends(get_session)):
    return tariff_service.create(session, payload)


@tariff.get("/store/{store_id}", status_code=status.HTTP_200_OK)
def get_by_store(store_id: int, session: Session = Depends(get_session)):
    return tariff_service.get_by_store_id(session, store_id)


@tariff.get("/store/{store_id}/template", status_code=status.HTTP_200_OK)
def download_template(store_id: int, session: Session = Depends(get_session)):
    # Valida que la tienda exista antes de servir la plantilla
    tariff_service._get_store_or_raise(session, store_id)
    excel_file = tariff_service.export_template()
    return StreamingResponse(
        excel_file,
        media_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition": "attachment; filename=plantilla_tarifas.xlsx"
        },
    )


@tariff.post("/store/{store_id}/import", status_code=status.HTTP_201_CREATED)
async def import_tariffs(
    store_id: int,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise BadRequestException(
            "Debe enviar un archivo Excel con extensión .xlsx."
        )

    file_content = await file.read()
    if not file_content:
        raise BadRequestException("El archivo Excel está vacío.")

    return tariff_service.import_from_excel(session, store_id, file_content)


@tariff.get("/{tariff_id}", status_code=status.HTTP_200_OK)
def get_by_id(tariff_id: int, session: Session = Depends(get_session)):
    return tariff_service.get_by_id(session, tariff_id)


@tariff.put("/{tariff_id}", status_code=status.HTTP_200_OK)
def update(
    tariff_id: int,
    payload: TariffUpdate,
    session: Session = Depends(get_session),
):
    return tariff_service.update(session, tariff_id, payload)


@tariff.delete("/{tariff_id}", status_code=status.HTTP_200_OK)
def delete(tariff_id: int, session: Session = Depends(get_session)):
    return tariff_service.delete(session, tariff_id)
