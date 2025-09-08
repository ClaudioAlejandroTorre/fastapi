from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import random
import string

# ------------------------
# Configuración Base de Datos
# ------------------------
DATABASE_URL = "postgresql://laburantes_db_user:mtNUViyTddNAbZhAVZP6R23G9k0BFcJY@dpg-d1m3kqa4d50c738f4a7g-a:5432/laburantes_db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# ------------------------
# Modelos
# ------------------------
class Trabajador(Base):
    __tablename__ = "trabajadores"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    clave_unica = Column(String, unique=True, index=True, nullable=False)
    aviso = Column(Text, default="")  # Solo 1 aviso editable por trabajador

Base.metadata.create_all(bind=engine)

# ------------------------
# Schemas
# ------------------------
class RegistroIn(BaseModel):
    nombre: str

class AvisoIn(BaseModel):
    clave_unica: str
    aviso: str

class AvisoOut(BaseModel):
    clave_unica: str
    aviso: str

# ------------------------
# App FastAPI
# ------------------------
app = FastAPI()

# Generar clave única aleatoria
def generar_clave_unica(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# ------------------------
# Endpoints
# ------------------------

@app.post("/registro/")
def registrar_trabajador(registro: RegistroIn):
    db = SessionLocal()
    # Verificar si ya existe trabajador con ese nombre (o criterio)
    trabajador_existente = db.query(Trabajador).filter_by(nombre=registro.nombre).first()
    if trabajador_existente:
        return {"clave_unica": trabajador_existente.clave_unica}

    # Crear nuevo trabajador con clave única
    clave = generar_clave_unica()
    nuevo = Trabajador(nombre=registro.nombre, clave_unica=clave)
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    db.close()
    return {"clave_unica": clave}

@app.post("/aviso/")
def guardar_aviso(aviso_in: AvisoIn):
    db = SessionLocal()
    trabajador = db.query(Trabajador).filter_by(clave_unica=aviso_in.clave_unica).first()
    if not trabajador:
        db.close()
        raise HTTPException(status_code=404, detail="Trabajador no encontrado")
    trabajador.aviso = aviso_in.aviso
    db.commit()
    db.close()
    return {"mensaje": "Aviso guardado correctamente"}

@app.get("/avisos/", response_model=List[AvisoOut])
def listar_avisos():
    db = SessionLocal()
    avisos = db.query(Trabajador).filter(Trabajador.aviso != "").all()
    db.close()
    return [{"clave_unica": t.clave_unica, "aviso": t.aviso} for t in avisos]
