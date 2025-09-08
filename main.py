from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import random
import string

# --- Configuración base de datos ---
DATABASE_URL = "postgresql://laburantes_db_user:mtNUViyTddNAbZhAVZP6R23G9k0BFcJY@dpg-d1m3kqa4d50c738f4a7g-a:5432/laburantes_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# --- Modelo Trabajador ---
class Trabajador(Base):
    __tablename__ = "trabajadores"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    dni = Column(String, nullable=True)
    wsapp = Column(String, nullable=True)
    penales = Column(String, nullable=True)
    correoElec = Column(String, nullable=True)
    clave_unica = Column(String, unique=True, nullable=False)

# --- Modelo Aviso ---
class Aviso(Base):
    __tablename__ = "avisos"
    id = Column(Integer, primary_key=True, index=True)
    texto = Column(Text, nullable=False)
    clave_unica = Column(String, nullable=False)  # propietario

Base.metadata.create_all(bind=engine)

# --- FastAPI app ---
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic schemas ---
class Registro(BaseModel):
    nombre: str
    dni: str | None = None
    wsapp: str | None = None
    penales: str | None = None
    correoElec: str | None = None

class AvisoIn(BaseModel):
    texto: str
    clave_unica: str

# --- Dependencia ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Generar clave única ---
def generar_clave_unica(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# --- Endpoints ---
@app.post("/registro/")
def registro(trabajador: Registro, db: Session = Depends(get_db)):
    # Validar si ya existe trabajador con mismo nombre/dni
    existe = db.query(Trabajador).filter_by(dni=trabajador.dni).first()
    if existe:
        return {"mensaje": "Trabajador ya existe", "clave_unica": existe.clave_unica}

    clave = generar_clave_unica()
    nuevo = Trabajador(
        nombre=trabajador.nombre,
        dni=trabajador.dni,
        wsapp=trabajador.wsapp,
        penales=trabajador.penales,
        correoElec=trabajador.correoElec,
        clave_unica=clave
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return {"mensaje": "Trabajador registrado", "clave_unica": clave}

@app.post("/avisos/")
def crear_aviso(aviso: AvisoIn, db: Session = Depends(get_db)):
    # Se permite crear cualquier aviso con su clave_unica
    nuevo = Aviso(texto=aviso.texto, clave_unica=aviso.clave_unica)
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return {"mensaje": "Aviso creado", "id": nuevo.id}

@app.get("/avisos/")
def listar_avisos(db: Session = Depends(get_db)):
    avisos = db.query(Aviso).all()
    return [{"id": a.id, "texto": a.texto, "editable": False} for a in avisos]

@app.patch("/avisos/{aviso_id}")
def editar_aviso(aviso_id: int, aviso: AvisoIn, db: Session = Depends(get_db)):
    a = db.query(Aviso).filter_by(id=aviso_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Aviso no encontrado")
    if a.clave_unica != aviso.clave_unica:
        raise HTTPException(status_code=403, detail="No puedes editar este aviso")
    a.texto = aviso.texto
    db.commit()
    db.refresh(a)
    return {"mensaje": "Aviso editado"}
