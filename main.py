from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import uuid
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # o tu dominio si querés restringir
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ----- DATABASE -----
DATABASE_URL = "postgresql://laburantes_db_user:mtNUViyTddNAbZhAVZP6R23G9k0BFcJY@dpg-d1m3kqa4d50c738f4a7g-a:5432/laburantes_db"
engine = create_engine(DATABASE_URL)
Base = declarative_base()

# ----- MODELOS -----
class Trabajador(Base):
    __tablename__ = "trabajadores"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, default="")     # opcional
    wsapp = Column(String, default="")
    aviso = Column(String, default="")
    foto = Column(String, nullable=True)    # URL o base64
    clave_unica = Column(String, unique=True, index=True)

Base.metadata.create_all(bind=engine)

# ----- Pydantic Schemas -----
class TrabajadorCreate(BaseModel):
    nombre: Optional[str] = ""
    wsapp: Optional[str] = ""

class AvisoUpdate(BaseModel):
    descripcion: Optional[str] = None
    foto_base64: Optional[str] = None

class AvisoOut(BaseModel):
    id: int
    nombre: str
    wsapp: str
    aviso: str
    foto: Optional[str] = None
    clave_unica: str

    class Config:
        orm_mode = True

# ----- DEPENDENCY -----
def get_db():
    db = Session(bind=engine)
    try:
        yield db
    finally:
        db.close()

# ----- APP -----
app = FastAPI()

# ----- ENDPOINTS -----

# Registro nuevo trabajador
@app.post("/registro/")
def crear_trabajador(db: Session = Depends(get_db)):
    clave_unica = str(uuid.uuid4())[:8]
    nuevo = Trabajador(clave_unica=clave_unica)
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return {"clave_unica": nuevo.clave_unica}

# Login con clave única
@app.get("/login_unico/{clave_unica}")
def login_unico(clave_unica: str, db: Session = Depends(get_db)):
    trabajador = db.query(Trabajador).filter_by(clave_unica=clave_unica).first()
    if not trabajador:
        raise HTTPException(status_code=404, detail="Clave no encontrada")
    return {
        "id": trabajador.id,
        "nombre": trabajador.nombre,
        "wsapp": trabajador.wsapp,
        "aviso": trabajador.aviso,
        "foto": trabajador.foto,
        "clave_unica": trabajador.clave_unica
    }

# Listar todos los avisos
@app.get("/avisos/", response_model=List[AvisoOut])
def listar_avisos(db: Session = Depends(get_db)):
    trabajadores = db.query(Trabajador).all()
    return trabajadores

# Editar aviso propio
@app.patch("/trabajadores/{clave_unica}")
def editar_aviso(clave_unica: str, data: AvisoUpdate, db: Session = Depends(get_db)):
    trabajador = db.query(Trabajador).filter_by(clave_unica=clave_unica).first()
    if not trabajador:
        raise HTTPException(status_code=404, detail="Clave no encontrada")

    if data.descripcion is not None:
        trabajador.aviso = data.descripcion
    if data.foto_base64 is not None:
        trabajador.foto = data.foto_base64  # puede almacenar base64 o URL

    db.commit()
    db.refresh(trabajador)
    return {"mensaje": "Aviso actualizado"}

# Eliminar aviso propio
@app.delete("/trabajadores/{clave_unica}")
def eliminar_aviso(clave_unica: str, db: Session = Depends(get_db)):
    trabajador = db.query(Trabajador).filter_by(clave_unica=clave_unica).first()
    if not trabajador:
        raise HTTPException(status_code=404, detail="Clave no encontrada")

    trabajador.aviso = ""
    trabajador.foto = None
    db.commit()
    return {"mensaje": "Aviso eliminado"}
