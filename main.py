from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base, Session
import os, uuid

# -------------------------------------------------
# 🔹 Configuración Base de Datos (Postgres en Render)
# -------------------------------------------------
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://usuario:password@host:5432/dbname"  # reemplazar por Render
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# -------------------------------------------------
# 🔹 Modelo
# -------------------------------------------------
class Trabajador(Base):
    __tablename__ = "trabajadores"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, default="")
    wsapp = Column(String, default="")
    penales = Column(String, default="")   # descripción
    clave_unica = Column(String, unique=True, index=True)

# Crear tablas (solo primera vez)
Base.metadata.create_all(bind=engine)

# -------------------------------------------------
# 🔹 FastAPI App
# -------------------------------------------------
app = FastAPI()

# Dependencia de DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------------------------------------
# 🔹 Endpoints
# -------------------------------------------------

@app.post("/registro/")
def registro(db: Session = Depends(get_db)):
    """Registrar un nuevo trabajador y generar clave única"""
    clave = str(uuid.uuid4())[:8]  # clave corta de 8 caracteres
    nuevo = Trabajador(clave_unica=clave, nombre="Nuevo", wsapp="")
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return {"clave_unica": nuevo.clave_unica}

@app.get("/login_unico/{clave}")
def login_unico(clave: str, db: Session = Depends(get_db)):
    """Login con clave única"""
    t = db.query(Trabajador).filter(Trabajador.clave_unica == clave).first()
    if not t:
        raise HTTPException(404, "Clave no encontrada")
    return {
        "id": t.id,
        "nombre": t.nombre,
        "wsapp": t.wsapp,
        "penales": t.penales,
        "clave_unica": t.clave_unica,
    }

@app.get("/trabajadores/")
def listar(db: Session = Depends(get_db)):
    """Listar todos los trabajadores"""
    return db.query(Trabajador).all()

@app.patch("/trabajadores/{clave}")
def actualizar_descripcion(clave: str, descripcion: str, db: Session = Depends(get_db)):
    """Actualizar solo la descripción del trabajador dueño de la clave"""
    t = db.query(Trabajador).filter(Trabajador.clave_unica == clave).first()
    if not t:
        raise HTTPException(404, "Clave no encontrada")
    t.penales = descripcion
    db.commit()
    db.refresh(t)
    return {"msg": "Descripción actualizada", "penales": t.penales}
