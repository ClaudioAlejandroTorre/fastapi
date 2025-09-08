from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
import random
import string

DATABASE_URL = "postgresql://usuario:password@host:puerto/dbname"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Trabajador(Base):
    __tablename__ = "trabajadores"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    dni = Column(String, nullable=False)
    penales = Column(String, nullable=True)
    wsapp = Column(String, nullable=True)
    clave_unica = Column(String, unique=True, nullable=False)

Base.metadata.create_all(bind=engine)

app = FastAPI()

# Pydantic models
class RegistroTrabajador(BaseModel):
    nombre: str
    dni: str
    penales: str = ""
    wsapp: str = ""

# Generar clave única
def generar_clave_unica(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# Registro
@app.post("/registro/")
def registro(trabajador: RegistroTrabajador):
    db = SessionLocal()
    clave = generar_clave_unica()
    nuevo = Trabajador(
        nombre=trabajador.nombre,
        dni=trabajador.dni,
        penales=trabajador.penales,
        wsapp=trabajador.wsapp,
        clave_unica=clave
    )
    db.add(nuevo)
    try:
        db.commit()
        db.refresh(nuevo)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
    return {"clave_unica": clave}

# Login con clave única
@app.get("/login_unico/{clave}")
def login_unico(clave: str):
    db = SessionLocal()
    trabajador = db.query(Trabajador).filter(Trabajador.clave_unica == clave).first()
    db.close()
    if not trabajador:
        raise HTTPException(status_code=404, detail="Clave no encontrada")
    return {
        "nombre": trabajador.nombre,
        "dni": trabajador.dni,
        "penales": trabajador.penales,
        "wsapp": trabajador.wsapp,
        "clave_unica": trabajador.clave_unica
    }
