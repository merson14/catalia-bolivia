import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

# Obtener la ruta absoluta de la carpeta actual (ej. backend/)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Definir la ruta exacta de la base de datos (si la carpeta 'database' está dentro de backend/)
# Si 'database' está un nivel más arriba (en la raíz), cambia a os.path.join(BASE_DIR, "..", "database", "catalia_local.db")
DB_PATH = os.path.join(BASE_DIR, "database", "catalia_local.db")

SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# Crear el motor de base de datos
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Sesión local
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Definición oficial de Base para SQLAlchemy 2.0
Base = declarative_base()

# Dependencia para las peticiones en FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()