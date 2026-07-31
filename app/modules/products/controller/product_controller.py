from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from app.database.session import get_session
from app.modules.products.schema.product_schema import ProductCreate, ProductUpdate
from app.modules.products.service.product_service import ProductService
from app.modules.shared.exceptions.app_exceptions import BadRequestException

product = APIRouter(
    prefix="/product",
    tags=["product"],
)

product_service = ProductService()


@product.post("", status_code=status.HTTP_201_CREATED)
def create(payload: ProductCreate, session: Session = Depends(get_session)):
    return product_service.create(session, payload)


@product.get("", status_code=status.HTTP_200_OK)
def get_all(session: Session = Depends(get_session)):
    return product_service.get_all(session)


@product.get("/store/{store_id}", status_code=status.HTTP_200_OK)
def get_by_store(store_id: int, session: Session = Depends(get_session)):
    return product_service.get_by_store_id(session, store_id)


@product.get("/store/{store_id}/export", status_code=status.HTTP_200_OK)
def export_products(store_id: int, session: Session = Depends(get_session)):
    excel_file = product_service.export_products_excel(session, store_id)

    return StreamingResponse(
        excel_file,
        media_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition": f"attachment; filename=productos_tienda_{store_id}.xlsx"
        },
    )


@product.post("/store/{store_id}/import", status_code=status.HTTP_201_CREATED)
async def import_products(
    store_id: int,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise BadRequestException("Debe enviar un archivo Excel con extensión .xlsx.")

    file_content = await file.read()

    if not file_content:
        raise BadRequestException("El archivo Excel está vacío.")

    return product_service.import_products_excel(session, store_id, file_content)


@product.get("/category/{category_id}", status_code=status.HTTP_200_OK)
def get_by_category(category_id: int, session: Session = Depends(get_session)):
    return product_service.get_by_category_id(session, category_id)


@product.get("/{product_id}", status_code=status.HTTP_200_OK)
def get_by_id(product_id: int, session: Session = Depends(get_session)):
    return product_service.get_by_id(session, product_id)


@product.put("/{product_id}", status_code=status.HTTP_200_OK)
def update(
    product_id: int,
    payload: ProductUpdate,
    session: Session = Depends(get_session),
):
    return product_service.update(session, product_id, payload)


@product.delete("/{product_id}", status_code=status.HTTP_200_OK)
def delete(product_id: int, session: Session = Depends(get_session)):
    return product_service.delete(session, product_id)
