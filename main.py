"""
main.py completo - FastAPI 3.13 / Render / Cloudinary / PostgreSQL
Usuarios: consultores y trabajadores
Trabajadores usan google_id para login seguro y edición de su propio aviso
"""

from datetime import datetime, timezone
from typing import Annotated, List
from fastapi import FastAPI, HTTPException, Depends, Query, Body, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, Float, String, ForeignKey, DateTime, select
from sqlalchemy.orm import declarative_base, relationship, Session, joinedload
import cloudinary
import cloudinary.uploader

# ----------------- CONFIGURACIÓN CLOUDINARY -----------------
cloudinary.config(
    cloud_name='dnlios4ua',
    api_key='747777351831491',
    api_secret='mvqCvHtSJYQHgKhtEwAfsHw93FI',
    secure=True
)

# ----------------- DATABASE POSTGRESQL -----------------
DATABASE_URL = "postgresql://laburantes_db_user:mtNUViyTddNAbZhAVZP6R23G9k0BFcJY@dpg-d1m3kqa4d50c738f4a7g-a:5432/laburantes_db"
engine = create_engine(DATABASE_URL)
Base = declarative_base()

# ----------------- MODELOS SQLALCHEMY -----------------
class Usuario(Base):
    __tablename__ = 'usuarios'
    id = Column(Integer, primary_key=True)
    nombre = Column(String, nullable=False)
    dni = Column(String, nullable=False)
    correoElec = Column(String, nullable=False)
    direccion = Column(String, nullable=False)
    localidad = Column(String, nullable=False)
    wsapp = Column(String, nullable=False)
    servicios_trabajadores = relationship("Servicios_Trabajadores", secondary="usuarios_servicios_trabajadores", back_populates='usuarios')

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
    google_id = Column(String, unique=True, nullable=True)  # <-- Para Sign-In
    servicios = relationship("Servicio", secondary="servicios_trabajadores", back_populates='trabajadores')

class Opinion(Base):
    __tablename__ = 'opiniones'
    id = Column(Integer, primary_key=True, index=True)
    trabajador_id = Column(Integer)
    comentario = Column(String, nullable=False)
    calificacion = Column(Integer, nullable=False)
    fecha = Column(DateTime, default=datetime.now(timezone.utc))

class Servicio(Base):
    __tablename__ = 'servicios'
    id = Column(Integer, primary_key=True)
    titulo = Column(String, nullable=False)
    trabajadores = relationship("Trabajador", secondary="servicios_trabajadores", back_populates='servicios')

class Servicios_Trabajadores(Base):
    __tablename__ = 'servicios_trabajadores'
    servicio_id = Column(Integer, ForeignKey('servicios.id'), primary_key=True)
    trabajador_id = Column(Integer, ForeignKey('trabajadores.id'), primary_key=True)
    precioxhora = Column(Integer)
    usuarios = relationship("Usuario", secondary="usuarios_servicios_trabajadores", back_populates='servicios_trabajadores')

class Usuarios_Servicios_Trabajadores(Base):
    __tablename__ = 'usuarios_servicios_trabajadores'
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), primary_key=True)
    servicio_trabajador_id = Column(Integer, ForeignKey('servicios_trabajadores.servicio_id'), primary_key=True)

class Tracking(Base):
    __tablename__ = 'tracking'
    id = Column(Integer, primary_key=True, autoincrement=True)
    fecha_hora = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    latitud = Column(Float, nullable=False)
    longitud = Column(Float, nullable=False)
    id_android = Column(String, nullable=False)

# ----------------- MODELOS Pydantic -----------------
class TrabajadorBase(BaseModel):
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
    google_id: str | None = None

class DescripcionUpdate(BaseModel):
    descripcion: str

class FotoUpdate(BaseModel):
    nueva_foto_url: str
    vieja_foto_url: str | None = None

class DeleteFotoRequest(BaseModel):
    foto_url: str

class OpinionCreate(BaseModel):
    comentario: str
    calificacion: int

class TrabajadorPublic(BaseModel):
    id: int
    nombre: str
    penales: str
    class Config:
        orm_mode = True

# ----------------- DEPENDENCIA DB -----------------
def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

# ----------------- APP CONFIG -----------------
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="fotos"), name="static")

# ----------------- ENDPOINTS -----------------

@app.post("/registro/", status_code=status.HTTP_201_CREATED)
def crear_trabajador(trabajador: TrabajadorBase, session: SessionDep):
    # Solo un trabajador por google_id
    if trabajador.google_id:
        existente = session.query(Trabajador).filter_by(google_id=trabajador.google_id).first()
        if existente:
            return {"mensaje": "Trabajador ya existe", "id": existente.id}

    nuevo = Trabajador(**trabajador.dict())
    session.add(nuevo)
    session.commit()
    session.refresh(nuevo)
    return {"mensaje": "Registro exitoso", "id": nuevo.id}

@app.patch("/trabajadores/{trabajador_id}", response_model=TrabajadorPublic)
def update_penales(
    *,
    session: SessionDep,
    trabajador_id: int,
    descripcion: str = Query(...)
):
    db_trabajador = session.get(Trabajador, trabajador_id)
    if not db_trabajador:
        raise HTTPException(status_code=404, detail="Trabajador not found")
    db_trabajador.penales = descripcion
    session.add(db_trabajador)
    session.commit()
    session.refresh(db_trabajador)
    return db_trabajador

@app.put("/trabajadores/{trabajador_id}/foto")
def update_foto(
    *,
    session: SessionDep,
    trabajador_id: int,
    payload: FotoUpdate
):
    db_trabajador = session.get(Trabajador, trabajador_id)
    if not db_trabajador:
        raise HTTPException(status_code=404, detail="Trabajador no encontrado")
    db_trabajador.foto = payload.nueva_foto_url
    session.add(db_trabajador)
    session.commit()
    session.refresh(db_trabajador)
    if payload.vieja_foto_url:
        try:
            public_id = payload.vieja_foto_url.split("/")[-1].split(".")[0]
            cloudinary.uploader.destroy(public_id)
        except Exception as e:
            print(f"⚠️ No se pudo eliminar la foto vieja: {e}")
    return {"msg": "Foto actualizada correctamente", "trabajador_id": trabajador_id, "nueva_foto": db_trabajador.foto}

@app.delete("/trabajadores/foto")
def delete_foto(payload: DeleteFotoRequest = Body(...)):
    try:
        public_id = payload.foto_url.split("/")[-1].split(".")[0]
        result = cloudinary.uploader.destroy(public_id)
        if result.get("result") not in ("ok", "not_found"):
            raise HTTPException(status_code=400, detail=f"Error eliminando foto: {result}")
        return {"msg": "Foto eliminada correctamente", "public_id": public_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error eliminando foto: {e}")

@app.post("/tracking/", status_code=status.HTTP_201_CREATED)
def crear_tracking(tracking: Tracking, session: SessionDep):
    session.add(tracking)
    session.commit()
    session.refresh(tracking)
    return {"mensaje": "Tracking registrado", "id": tracking.id}

# ----------------- CREAR TABLAS -----------------
Base.metadata.create_all(engine)
