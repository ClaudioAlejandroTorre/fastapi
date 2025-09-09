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
#DATABASE_URL = "sqlite:///./trabajadores.db"  # Cambiar a PostgreSQL si se desea
# SQLite local en la carpeta del proyecto
DATABASE_URL = "sqlite:///C:/Users/claud/AppData/Local/Programs/Python/Python313/ProyectoApi/trabajadores.db"

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

from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import List
from models import Trabajador  # tu clase ya definida

app = FastAPI()

# --- mismo engine y sesión que usas en /avisos/ ---
engine = create_engine("sqlite:///trabajadores.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

# --- endpoint de login por clave única ---
@app.get("/login_unico/{clave}")
def login_unico(clave: str):
    db = SessionLocal()
    try:
        trabajador = db.query(Trabajador).filter(Trabajador.clave_unica == clave).first()
        if not trabajador:
            raise HTTPException(status_code=404, detail="Trabajador no encontrado")
        # devolvemos los datos necesarios para App.js / Appi.js
        return {
            "nombre": trabajador.nombre,
            "clave_unica": trabajador.clave_unica,
            "aviso": trabajador.aviso
        }
    finally:
        db.close()

