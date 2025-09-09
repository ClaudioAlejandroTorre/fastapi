from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi.middleware.cors import CORSMiddleware
import uuid

DATABASE_URL = "postgresql://laburantes_db_user:mtNUViyTddNAbZhAVZP6R23G9k0BFcJY@dpg-d1m3kqa4d50c738f4a7g-a:5432/laburantes_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Make the DeclarativeMeta
Base = declarative_base()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ------------------ MODELO DB ------------------
class Trabajador(Base):
    __tablename__ = "trabajadores"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    dni = Column(String, index=True)  # 👈 ahora obligatorio en DB
    clave_unica = Column(String, unique=True, index=True)

Base.metadata.create_all(bind=engine)

# ------------------ SCHEMAS ------------------
class TrabajadorCreate(BaseModel):
    nombre: str
    dni: str

class TrabajadorOut(BaseModel):
    nombre: str
    dni: str
    clave_unica: str

# ------------------ DEPENDENCIA DB ------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ------------------ ENDPOINT ------------------
@app.post("/registro/", response_model=TrabajadorOut)
def crear_trabajador(trabajador: TrabajadorCreate, db: Session = Depends(get_db)):
    if not trabajador.dni:
        raise HTTPException(status_code=400, detail="DNI es obligatorio")

    clave = str(uuid.uuid4())[:8]  # Clave corta
    nuevo = Trabajador(
        nombre=trabajador.nombre,
        dni=trabajador.dni,
        clave_unica=clave
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo
# -------------------------------------------
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok", "message": "Backend FastAPI corriendo en Render 🚀"}