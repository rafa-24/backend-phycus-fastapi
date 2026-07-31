from fastapi import FastAPI
from fastapi.concurrency import run_in_threadpool
from app.database.init_db import create_db
from app.modules.helpers.analyze_images import rank_images
from app.modules.helpers.search_images_products import search_images_products
from app.modules.ranking.controller import ranking_controller
from app.modules.ranking.models import ranking_products
from app.modules.users.controller.user_controller import user
from app.modules.auth.controller.auth_controller import auth
from app.modules.stores.controller.store_controller import store
from app.modules.categories.controller.category_controller import category
from app.modules.products.controller.product_controller import product
from app.modules.collaborators.controller.collaborator_controller import collaborator
from app.modules.discounts.controller.discount_controller import discount
from app.modules.role.controller.role_controller import role
from app.modules.tariffs.controller.tariff_controller import tariff
from app.modules.shared.exceptions.exception_handlers import register_exception_handlers
from app.modules.ranking.controller.ranking_controller import ranking

from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="Phycus API", version="0.0.2")

# Defino las rutas que pueden enviar peticiones a phycus
origins = [
    "http://192.168.10.17:3000",
    "http://localhost:3000"
]

# metodos permitidos
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

@app.on_event("startup")
async def startup():
    create_db()

@app.get("/")
async def root():
    try:
        urls = await run_in_threadpool(
            search_images_products,
            "Buscar imagen del producto Mini Bites Vainilla identificado con codigo ean: 500645",
            max_results= 3
        )

        ranking = rank_images(
            name="Mini Bites Vainilla",
            ean_code="500645",
            image_urls=urls
        )

        return {
            "ranking": ranking
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise e

# incluir rutas en mi aplicacion
app.include_router(user)
app.include_router(auth)
app.include_router(store)
app.include_router(category)
app.include_router(product)
app.include_router(collaborator)
app.include_router(discount)
app.include_router(role)
app.include_router(ranking)
app.include_router(tariff)