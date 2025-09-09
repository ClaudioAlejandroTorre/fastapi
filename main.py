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
    wsapp = Column(String, nullable=False, default="")  # <--- obligatorio
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
    db = Session(bind=engine)
    try:
        yield db
    finally:
        db.close()
#--------------------------------------------
@app.get("/")
def root():
    return {"status": "ok", "message": "Backend FastAPI corriendo en Render 🚀"}
# ------------------ ENDPOINT ------------------
@app.post("/registro/")
def crear_trabajador(trabajador: TrabajadorCreate):
    db = SessionLocal()
    try:
        clave_unica = uuid.uuid4().hex[:8]
        nuevo = Trabajador(
            nombre=trabajador.nombre,
            dni=trabajador.dni,
            wsapp=trabajador.wsapp or "",  # <--- nunca NULL
            clave_unica=clave_unica
        )
        db.add(nuevo)
        db.commit()
        db.refresh(nuevo)
        return {"id": nuevo.id, "clave_unica": clave_unica}
    finally:
        db.close()

# -------------------------------------------
