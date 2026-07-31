from datetime import UTC, datetime
from decimal import Decimal

from sqlmodel import Session

from app.modules.shared.exceptions.app_exceptions import (
    BadRequestException,
    InternalServerException,
    NotFoundException,
)
from app.modules.shared.schemas.api_response import ApiResponse
from app.modules.stores.repository.store_repository import StoreRepository
from app.modules.tariffs.models.tariff_model import Tariffs
from app.modules.tariffs.repository.tariff_repository import TariffRepository
from app.modules.tariffs.schema.tariff_schema import (
    TariffCreate,
    TariffImportResponse,
    TariffImportSkippedRow,
    TariffResponse,
    TariffUpdate,
)
from app.modules.tariffs.utils.excel import (
    create_tariffs_template,
    parse_tariffs_workbook,
)


class TariffService:
    def __init__(self):
        self.tariff_repository = TariffRepository()
        self.store_repository = StoreRepository()

    def _get_store_or_raise(self, session: Session, store_id: int):
        store = self.store_repository.get_by_id(session, store_id)
        if not store:
            raise NotFoundException(
                "No existe una tienda con el identificador indicado."
            )
        return store

    def _get_tariff_or_raise(self, session: Session, tariff_id: int) -> Tariffs:
        tariff = self.tariff_repository.get_by_id(session, tariff_id)
        if not tariff:
            raise NotFoundException(
                "No existe una tarifa con el identificador indicado."
            )
        return tariff

    def create(self, session: Session, payload: TariffCreate):
        store = self._get_store_or_raise(session, payload.store_id)

        if not payload.localidad.strip() or not payload.barrio.strip():
            raise BadRequestException("Localidad y barrio son obligatorios.")

        city = (payload.city or store.city or "Barranquilla").strip()

        tariff = Tariffs(
            store_id=payload.store_id,
            localidad=payload.localidad.strip(),
            barrio=payload.barrio.strip(),
            tarifa=payload.tarifa,
            tarifa_enrutar=payload.tarifa_enrutar,
            lat=payload.lat,
            lng=payload.lng,
            city=city or "Barranquilla",
            is_active=payload.is_active,
        )

        created = self.tariff_repository.create(session, tariff)
        if created.id is None:
            raise InternalServerException("No fue posible crear la tarifa.")

        return ApiResponse(
            message="La tarifa se creó de manera exitosa.",
            data=TariffResponse.model_validate(created),
        )

    def get_by_store_id(self, session: Session, store_id: int):
        self._get_store_or_raise(session, store_id)
        tariffs = self.tariff_repository.get_by_store_id(session, store_id)
        return ApiResponse(
            message="Tarifas obtenidas correctamente.",
            data=[TariffResponse.model_validate(item) for item in tariffs],
        )

    def get_by_id(self, session: Session, tariff_id: int):
        tariff = self._get_tariff_or_raise(session, tariff_id)
        return ApiResponse(
            message="Tarifa obtenida correctamente.",
            data=TariffResponse.model_validate(tariff),
        )

    def update(self, session: Session, tariff_id: int, payload: TariffUpdate):
        tariff = self._get_tariff_or_raise(session, tariff_id)
        update_data = payload.model_dump(exclude_unset=True)

        if not update_data:
            raise BadRequestException("No se enviaron datos para actualizar la tarifa.")

        for field, value in update_data.items():
            if isinstance(value, str):
                value = value.strip()
            setattr(tariff, field, value)

        tariff.updated_at = datetime.now(UTC)
        updated = self.tariff_repository.update(session, tariff)

        return ApiResponse(
            message="La tarifa se actualizó de manera exitosa.",
            data=TariffResponse.model_validate(updated),
        )

    def delete(self, session: Session, tariff_id: int):
        tariff = self._get_tariff_or_raise(session, tariff_id)
        self.tariff_repository.delete(session, tariff)
        return ApiResponse(
            message="La tarifa se eliminó de manera exitosa.",
            data=TariffResponse.model_validate(tariff),
        )

    def export_template(self):
        return create_tariffs_template()

    def import_from_excel(
        self, session: Session, store_id: int, file_content: bytes
    ):
        store = self._get_store_or_raise(session, store_id)
        default_city = (store.city or "Barranquilla").strip() or "Barranquilla"

        try:
            parsed_rows = parse_tariffs_workbook(file_content)
        except ValueError as exc:
            raise BadRequestException(str(exc)) from exc

        if not parsed_rows:
            raise BadRequestException(
                "No se encontraron filas válidas en el archivo Excel."
            )

        created_count = 0
        updated_count = 0
        skipped_rows: list[TariffImportSkippedRow] = []
        result_tariffs: list[Tariffs] = []
        current_localidad = ""

        for row in parsed_rows:
            if "error" in row:
                skipped_rows.append(
                    TariffImportSkippedRow(
                        row_number=row["row_number"],
                        reason=row["error"],
                        localidad=row.get("localidad"),
                        barrio=row.get("barrio"),
                    )
                )
                continue

            localidad = row["localidad"] or current_localidad
            if row["localidad"]:
                current_localidad = row["localidad"]

            if not localidad:
                skipped_rows.append(
                    TariffImportSkippedRow(
                        row_number=row["row_number"],
                        reason="No se pudo determinar la localidad.",
                        barrio=row.get("barrio"),
                    )
                )
                continue

            barrio = row["barrio"]
            city = row.get("city") or default_city
            existing = self.tariff_repository.get_by_store_and_barrio(
                session, store_id, barrio, localidad
            )

            if existing:
                existing.tarifa = row.get("tarifa")
                existing.tarifa_enrutar = row.get("tarifa_enrutar")
                existing.city = city
                existing.is_active = row.get("is_active", True)
                existing.updated_at = datetime.now(UTC)
                updated = self.tariff_repository.update(session, existing)
                result_tariffs.append(updated)
                updated_count += 1
            else:
                tariff = Tariffs(
                    store_id=store_id,
                    localidad=localidad,
                    barrio=barrio,
                    tarifa=row.get("tarifa"),
                    tarifa_enrutar=row.get("tarifa_enrutar"),
                    city=city,
                    is_active=row.get("is_active", True),
                )
                created = self.tariff_repository.create(session, tariff)
                result_tariffs.append(created)
                created_count += 1

        return ApiResponse(
            message="Importación de tarifas finalizada.",
            data=TariffImportResponse(
                tariffs_created=created_count,
                tariffs_updated=updated_count,
                rows_skipped=len(skipped_rows),
                skipped_rows=skipped_rows,
                tariffs=[
                    TariffResponse.model_validate(item) for item in result_tariffs
                ],
            ),
        )
