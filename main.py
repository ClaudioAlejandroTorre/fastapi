from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import random
import string

DATABASE_URL = "postgresql://laburantes_db_user:mtNUViyTddNAbZhAVZP6R23G9k0BFcJY@dpg-d1m3kqa4d50c738f4a7g-a:5432/laburantes_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()

# Modelo Trabajador
class Trabajador(Base):
    __tablename__ = "trabajadores"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    dni = Column(String, nullable=False)
    wsapp = Column(String, nullable=True)
    penales = Column(String, nullable=True)
    correoElec = Column(String, nullable=True)
    clave_unica = Column(String, unique=True, nullable=False)

Base.metadata.create_all(bind=engine)

# Schemas
class Registro(BaseModel):
    nombre: str
    dni: str
    wsapp: str = ""
    penales: str = ""
    correoElec: str = None

class LoginUnico(BaseModel):
    clave_unica: str

app = FastAPI()

# Genera clave única aleatoria
def generar_clave_unica(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# Endpoint de registro
@app.post("/registro/")
def registro(trabajador: Registro):
    db = SessionLocal()
    try:
        clave = generar_clave_unica()
        nuevo_trabajador = Trabajador(
            nombre=trabajador.nombre,
            dni=trabajador.dni,
            wsapp=trabajador.wsapp,
            penales=trabajador.penales,
            correoElec=trabajador.correoElec,
            clave_unica=clave
        )
        db.add(nuevo_trabajador)
        db.commit()
        db.refresh(nuevo_trabajador)
        return {"clave_unica": clave, "id": nuevo_trabajador.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

# Endpoint para login usando clave única
@app.post("/login_unico/")
def login_unico(data: LoginUnico):
    db = SessionLocal()
    try:
        trabajador = db.query(Trabajador).filter_by(clave_unica=data.clave_unica).first()
        if not trabajador:
            raise HTTPException(status_code=404, detail="Trabajador no encontrado")
        return {
            "nombre": trabajador.nombre,
            "dni": trabajador.dni,
            "wsapp": trabajador.wsapp,
            "penales": trabajador.penales,
            "correoElec": trabajador.correoElec,
            "clave_unica": trabajador.clave_unica
        }
    finally:
        db.close()
