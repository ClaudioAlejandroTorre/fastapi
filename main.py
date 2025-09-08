from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import sessionmaker, declarative_base
import random, string

DATABASE_URL = "postgresql://laburantes_db_user:mtNUViyTddNAbZhAVZP6R23G9k0BFcJY@dpg-d1m3kqa4d50c738f4a7g-a:5432/laburantes_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Trabajador(Base):
    __tablename__ = "trabajadores"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    clave_unica = Column(String, unique=True, nullable=False)
    aviso = Column(Text, default="")  # solo 1 aviso por trabajador

Base.metadata.create_all(bind=engine)

app = FastAPI()

class RegistroIn(BaseModel):
    nombre: str

class AvisoIn(BaseModel):
    clave_unica: str
    aviso: str

class AvisoOut(BaseModel):
    nombre: str
    aviso: str
    editable: bool

def generar_clave_unica():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=7))

@app.post("/registro/")
def registro(data: RegistroIn):
    db = SessionLocal()
    clave = generar_clave_unica()
    trabajador = Trabajador(nombre=data.nombre, clave_unica=clave)
    db.add(trabajador)
    db.commit()
    db.refresh(trabajador)
    db.close()
    return {"clave_unica": clave}

@app.post("/guardar_aviso/")
def guardar_aviso(data: AvisoIn):
    db = SessionLocal()
    trabajador = db.query(Trabajador).filter_by(clave_unica=data.clave_unica).first()
    if not trabajador:
        db.close()
        raise HTTPException(status_code=404, detail="Trabajador no encontrado")
    trabajador.aviso = data.aviso
    db.commit()
    db.refresh(trabajador)
    db.close()
    return {"status": "ok"}

@app.get("/avisos/{clave_unica}", response_model=List[AvisoOut])
def ver_avisos(clave_unica: str):
    db = SessionLocal()
    todos = db.query(Trabajador).all()
    salida = []
    for t in todos:
        salida.append(AvisoOut(
            nombre=t.nombre,
            aviso=t.aviso,
            editable=(t.clave_unica == clave_unica)
        ))
    db.close()
    return salida
