from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import sessionmaker, declarative_base
import random, string

app = FastAPI()
DATABASE_URL = "postgresql://laburantes_db_user:mtNUViyTddNAbZhAVZP6R23G9k0BFcJY@dpg-d1m3kqa4d50c738f4a7g-a:5432/laburantes_db"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

class Trabajador(Base):
    __tablename__ = "trabajadores"
    id = Column(Integer, primary_key=True)
    nombre = Column(String, nullable=False)
    clave_unica = Column(String, nullable=False, unique=True)

class Aviso(Base):
    __tablename__ = "avisos"
    id = Column(Integer, primary_key=True)
    texto = Column(String, nullable=False)
    clave_unica = Column(String, nullable=False)

Base.metadata.create_all(bind=engine)

class Registro(BaseModel):
    nombre: str

class NuevoAviso(BaseModel):
    texto: str
    clave_unica: str

def generar_clave_unica():
    return "".join(random.choices(string.ascii_letters + string.digits, k=8))

@app.post("/registro/")
def registro(trab: Registro):
    db = Session()
    # Verificar si ya existe algún trabajador con esta clave única
    clave = generar_clave_unica()
    while db.query(Trabajador).filter_by(clave_unica=clave).first():
        clave = generar_clave_unica()

    nuevo = Trabajador(nombre=trab.nombre, clave_unica=clave)
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return {"clave_unica": nuevo.clave_unica}

@app.get("/avisos/")
def obtener_avisos():
    db = Session()
    avisos = db.query(Aviso).all()
    return [{"id": a.id, "texto": a.texto, "clave_unica": a.clave_unica} for a in avisos]

@app.post("/avisos/")
def crear_aviso(aviso: NuevoAviso):
    db = Session()
    nuevo = Aviso(texto=aviso.texto, clave_unica=aviso.clave_unica)
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return {"id": nuevo.id, "texto": nuevo.texto, "clave_unica": nuevo.clave_unica}
