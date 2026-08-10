from fastapi import FastAPI
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
from app.modules.integrations.payments.bold.controller.bold_controller import bold
from app.modules.orders.controller.order_controller import order
from app.modules.integrations.siigo.controller.sigo_detail_controller import siigo
from app.modules.analytics.controller.analytics_controller import analytics



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
def startup():
    create_db()

@app.get("/")
def root():
    return {
        "message": 'Bienvenido a phycus V.1.0.1'
    }


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
app.include_router(bold)
app.include_router(order)
app.include_router(siigo)
app.include_router(analytics)