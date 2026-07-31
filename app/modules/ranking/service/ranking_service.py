from fastapi.concurrency import run_in_threadpool
from sqlmodel import Session

from app.modules.helpers.analyze_images import rank_images
from app.modules.helpers.search_images_products import search_images_products
from app.modules.products.models.product_model import Products
from app.modules.products.repository.product_repository import ProductRepository
from app.modules.ranking.models.ranking_products import Ranking
from app.modules.ranking.repository.ranking_repository import RankingRepository
from app.modules.ranking.schema.ranking_schema import RankingResponse
from app.modules.shared.exceptions.app_exceptions import (
    BadRequestException,
    ConflictException,
    InternalServerException,
    NotFoundException,
)
from app.modules.shared.schemas.api_response import ApiResponse


class RankingService:
    def __init__(self) -> None:
        self.ranking_repository = RankingRepository()
        self.product_repository = ProductRepository()

    def _get_product_or_raise(self, session: Session, product_id: int) -> Products:
        product = self.product_repository.get_by_id(session, product_id)

        if product is None:
            raise NotFoundException(
                "No existe un producto con el identificador indicado."
            )

        return product

    def _build_search_query(self, product: Products) -> str:
        return f"{product.name} codigo EAN 5449000000996"

    async def _generate_and_save_ranking(
        self,
        session: Session,
        product: Products,
        max_results: int = 3,
    ) -> list[Ranking]:
        query = self._build_search_query(product)

        urls = await run_in_threadpool(
            search_images_products,
            query,
            max_results=max_results,
        )

        if not urls:
            raise BadRequestException(
                "No se encontraron imágenes para generar el ranking."
            )

        ranking_results = rank_images(name=product.name, image_urls=urls)

        if not ranking_results:
            raise BadRequestException(
                "No fue posible rankear las imágenes del producto."
            )

        saved_rankings: list[Ranking] = []

        for item in ranking_results:
            ranking = Ranking(
                product_id=product.id,
                score=item["score"],
                reason=item["explicacion"],
                image_url=item["image_url"],
            )
            saved_ranking = self.ranking_repository.create(session, ranking)

            if saved_ranking.id is None:
                raise InternalServerException(
                    "No fue posible guardar el ranking de imágenes."
                )

            saved_rankings.append(saved_ranking)

        return saved_rankings

    async def create(self, session: Session, product_id: int):
        product = self._get_product_or_raise(session, product_id)

        existing_ranking = self.ranking_repository.get_by_product_id(
            session, product_id
        )

        if existing_ranking:
            raise ConflictException(
                "Este producto ya tiene un ranking de imágenes. "
                "Usa PUT /ranking/{product_id} para actualizarlo."
            )

        saved_rankings = await self._generate_and_save_ranking(session, product)

        return ApiResponse(
            message="Se guardó el ranking de imágenes de manera correcta.",
            data=[
                RankingResponse.model_validate(item) for item in saved_rankings
            ],
        )

    async def update(self, session: Session, product_id: int):
        product = self._get_product_or_raise(session, product_id)

        self.ranking_repository.delete_by_product_id(session, product_id)

        saved_rankings = await self._generate_and_save_ranking(session, product)

        return ApiResponse(
            message="El ranking de imágenes se actualizó de manera exitosa.",
            data=[
                RankingResponse.model_validate(item) for item in saved_rankings
            ],
        )

    def get_ranking(self, session: Session):
        ranking_list = self.ranking_repository.get(session)

        if len(ranking_list) == 0:
            return ApiResponse(
                message="Aún no has generado imágenes para tus productos.",
                data=[],
            )

        return ApiResponse(
            message="Lista de ranking de imágenes.",
            data=[RankingResponse.model_validate(item) for item in ranking_list],
        )

    def get_images_by_id(self, session: Session, product_id: int):
        product = self._get_product_or_raise(session, product_id)

        product_images = self.ranking_repository.get_by_product_id(
            session, product.id
        )

        return ApiResponse(
            message="Ranking de imágenes del producto.",
            data=[RankingResponse.model_validate(item) for item in product_images],
        )

    def delete_by_product_id(self, session: Session, product_id: int):
        self._get_product_or_raise(session, product_id)

        deleted_rankings = self.ranking_repository.delete_by_product_id(
            session, product_id
        )

        if not deleted_rankings:
            raise NotFoundException(
                "No hay ranking de imágenes para este producto."
            )

        return ApiResponse(
            message="El ranking de imágenes se eliminó de manera exitosa.",
            data=[
                RankingResponse.model_validate(item) for item in deleted_rankings
            ],
        )
