import os
from dotenv import load_dotenv
from sqlmodel import  create_engine

# 1. Cargar el archivo .env en las variables de entorno de la app
load_dotenv()

# 2. Obtener la cadena de conexión del entorno
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError('No existe variable de conexion en el .env')

# 3. Crear el Engine de SQLAlchemy
# Asegúrate de que DATABASE_URL en tu .env empiece por:
# sqlitecloud://usuario:password@host.sqlite.cloud:8860/nombre_db
engine = create_engine(
    DATABASE_URL,
    connect_args= {},
    echo= True
)
