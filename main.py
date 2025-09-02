from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Depends, status, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, Float, String, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship, Session, joinedload
from pydantic import BaseModel
from typing import List, Annotated, Optional
import cloudinary
import cloudinary.uploader
import os

# Config Cloudinary
cloudinary.config(
    cloud_name='dnlios4ua',
    api_key='747777351831491',
    api_secret='mvqCvHtSJYQHgKhtEwAfsHw93FI',
    secure=True
)

# DB URL PostgreSQL
DATABASE_URL = "postgresql://laburantes_db_user:mtNUViyTddNAbZhAVZP6R23G9k0BFcJY@dpg-d1m3kqa4d50c738f4a7g-a:5432/laburantes_db"
engine = create_engine(DATABASE_URL)
Base = declarative_base()

# CORS
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="fotos"), name="static")

# -------------------- MODELOS --------------------

class Trabajador(Base):
    __tablename__ = 'trabajadores'
    id = Column(Integer, primary_key=True)
    nombre = Column(String, nullable=False)
    dni = Column(String, nullable=False)
    correoElec = Column(String, nullable=False)
    direccion = Column(String, nullable=False)
    localidad = Column(String, nullable=False)
    latitud = Column(Float)
    longitud = Column(Float)
    wsapp = Column(String, nullable=False)
    foto = Column(String, nullable=False)
    penales = Column(String, nullable=False)
    google_id = Column(String, nullable=False, unique=True)  # Nuevo campo
    servicios = relationship("Servicio", secondary="servicios_trabajadores", back_populates='trabajadores')

class Servicio(Base):
    __tablename__ = 'servicios'
    id = Column(Integer, primary_key=True)
    titulo = Column(String, nullable=False)
    trabajadores = relationship("Trabajador", secondary="servicios_trabajadores", back_populates='servicios')

class Servicios_Trabajadores(Base):
    __tablename__ = 'servicios_trabajadores'
    id = Column(Integer, primary_key=True, autoincrement=True)
    servicio_id = Column(Integer, ForeignKey('servicios.id'))
    trabajador_id = Column(Integer, ForeignKey('trabajadores.id'))
    precioxhora = Column(Integer)

class Opinion(Base):
    __tablename__ = 'opiniones'
    id = Column(Integer, primary_key=True, index=True)
    trabajador_id = Column(Integer, nullable=False)
    comentario = Column(String, nullable=False)
    calificacion = Column(Integer, nullable=False)
    fecha = Column(DateTime, default=datetime.now(timezone.utc))

# -------------------- SCHEMAS --------------------

class TrabajadorCreate(BaseModel):
    nombre: str
    dni: str
    correoElec: str
    direccion: str
    localidad: str
    latitud: float
    longitud: float
    wsapp: str
    foto: str
    penales: str
    google_id: str

class TrabajadorUpdate(BaseModel):
    correoElec: Optional[str]
    direccion: Optional[str]
    localidad: Optional[str]
    latitud: Optional[float]
    longitud: Optional[float]
    wsapp: Optional[str]
    penales: Optional[str]

class OpinionCreate(BaseModel):
    comentario: str
    calificacion: int

# -------------------- DB SESSION --------------------

def get_db():
    db = Session(bind=engine)
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

# Crear tablas
Base.metadata.create_all(engine)

# -------------------- ENDPOINTS --------------------

@app.post("/registro/", status_code=status.HTTP_201_CREATED)
def crear_trabajador(trabajador: TrabajadorCreate, db: db_dependency):
    # Si ya existe google_id → no duplicar
    existing = db.query(Trabajador).filter(Trabajador.google_id == trabajador.google_id).first()
    if existing:
        return {"mensaje": "Trabajador ya existe", "id": existing.id}
    nuevo = Trabajador(**trabajador.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return {"mensaje": "Registro exitoso", "id": nuevo.id}

@app.patch("/trabajadores/{trabajador_id}")
def editar_trabajador(trabajador_id: int, google_id: str = Query(...), data: TrabajadorUpdate = Body(...), db: db_dependency = Depends(get_db)):
    t = db.query(Trabajador).filter(Trabajador.id == trabajador_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Trabajador no encontrado")
    if t.google_id != google_id:
        raise HTTPException(status_code=403, detail="No puede editar este aviso")
    for field, value in data.dict(exclude_unset=True).items():
        setattr(t, field, value)
    db.commit()
    db.refresh(t)
    return {"mensaje": "Aviso actualizado", "trabajador": t.id}

@app.delete("/trabajadores/{trabajador_id}")
def eliminar_trabajador(trabajador_id: int, google_id: str = Query(...), db: db_dependency = Depends(get_db)):
    t = db.query(Trabajador).filter(Trabajador.id == trabajador_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Trabajador no encontrado")
    if t.google_id != google_id:
        raise HTTPException(status_code=403, detail="No puede eliminar este aviso")
    # Borrar opiniones
    opiniones = db.query(Opinion).filter(Opinion.trabajador_id == trabajador_id).all()
    for op in opiniones:
        db.delete(op)
    # Borrar foto Cloudinary
    if t.foto:
        try:
            public_id = t.foto.split("/")[-1].split(".")[0]
            cloudinary.uploader.destroy(public_id)
        except:
            pass
    db.delete(t)
    db.commit()
    return {"mensaje": "Trabajador eliminado correctamente"}

@app.get("/Listo_trabajadoresPorServicio/{titulo_servicio}")
def listar_trabajadores(titulo_servicio: str, db: db_dependency):
    consulta = db.query(Servicio.titulo, Trabajador.id, Trabajador.nombre, Trabajador.penales, Trabajador.foto, Trabajador.wsapp, Trabajador.latitud, Trabajador.longitud, Trabajador.google_id)\
        .join(Servicios_Trabajadores, Servicio.id == Servicios_Trabajadores.servicio_id)\
        .join(Trabajador, Trabajador.id == Servicios_Trabajadores.trabajador_id)\
        .filter(Servicio.titulo == titulo_servicio).all()
    resultado = [
        {
            "servicio": row[0],
            "id": row[1],
            "nombre": row[2],
            "penales": row[3],
            "foto": row[4],
            "wsapp": row[5],
            "Latitud": row[6],
            "Longitud": row[7],
            "google_id": row[8]
        }
        for row in consulta
    ]
    return {"trabajadores": resultado}

@app.get("/opiniones_por_trabajador/{trabajador_id}")
def opiniones_por_trabajador(trabajador_id: int, db: db_dependency):
    return db.query(Opinion).filter(Opinion.trabajador_id == trabajador_id).order_by(Opinion.id.desc()).all()

@app.post("/opiniones/{trabajador_id}")
def crear_opinion(trabajador_id: int, opinion: OpinionCreate, db: db_dependency):
    nueva = Opinion(trabajador_id=trabajador_id, comentario=opinion.comentario, calificacion=opinion.calificacion)
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return {"mensaje": "Opinión registrada", "id": nueva.id}
