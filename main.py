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
def crear_trabajador(data: dict):
    db = SessionLocal()
    nombre = data["nombre"].strip()

    # Verificar si ya existe un trabajador con ese nombre
    existente = db.query(Trabajador).filter(Trabajador.nombre == nombre).first()
    if existente:
        db.close()
        raise HTTPException(status_code=409, detail="El nombre ya está registrado. Usa tu clave única.")

    # Si no existe → crear nuevo
    clave = generar_clave_unica()
    trabajador = Trabajador(nombre=nombre, clave_unica=clave)
    db.add(trabajador)
    db.commit()
    db.refresh(trabajador)
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

@app.get("/avisos/")
def listar_avisos():
    db = SessionLocal()
    avisos = db.query(Trabajador).filter(Trabajador.aviso != "").all()
    db.close()
    return [
        {"clave_unica": t.clave_unica, "aviso": t.aviso, "nombre": t.nombre} 
        for t in avisos
    ]

@app.get("/login_unico/{clave}")
def login_unico(clave: str):
    db = SessionLocal()
    try:
        trabajador = db.query(Trabajador).filter(Trabajador.clave_unica == clave).first()
        if not trabajador:
            raise HTTPException(status_code=404, detail="Trabajador no encontrado")
        return {
            "nombre": trabajador.nombre,
            "clave_unica": trabajador.clave_unica,
            "aviso": trabajador.aviso
        }
    finally:
        db.close()

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.patch("/trabajadores/{clave_unica}/aviso")
def actualizar_aviso(clave_unica: str, data: dict, db: Session = Depends(get_db)):
    trabajador = db.query(Trabajador).filter(Trabajador.clave_unica == clave_unica).first()
    if not trabajador:
        return {"error": "Trabajador no encontrado"}

    aviso = data.get("aviso", "")
    trabajador.aviso = aviso
    db.commit()
    db.refresh(trabajador)
    return {
        "mensaje": "Aviso actualizado correctamente",
        "clave_unica": trabajador.clave_unica,
        "nombre": trabajador.nombre,
        "aviso": trabajador.aviso,
    }
    



