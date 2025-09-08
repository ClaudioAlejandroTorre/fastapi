from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "postgresql://laburantes_db_user:mtNUViyTddNAbZhAVZP6R23G9k0BFcJY@dpg-d1m3kqa4d50c738f4a7g-a:5432/laburantes_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

app = FastAPI()

# Modelos
class Trabajador(Base):
    __tablename__ = "trabajadores"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    clave_unica = Column(String, unique=True, nullable=False)

class Aviso(Base):
    __tablename__ = "avisos"
    id = Column(Integer, primary_key=True, index=True)
    texto = Column(String, nullable=False)
    clave_unica = Column(String, nullable=False)

Base.metadata.create_all(bind=engine)

# Schemas
class AvisoCreate(BaseModel):
    texto: str
    clave_unica: str

# Endpoints
@app.post("/avisos/")
def crear_aviso(aviso: AvisoCreate):
    db = SessionLocal()
    existe = db.query(Aviso).filter(Aviso.clave_unica == aviso.clave_unica).first()
    if existe:
        db.close()
        raise HTTPException(status_code=400, detail="Aviso ya existe para esta clave única")
    
    nuevo_aviso = Aviso(texto=aviso.texto, clave_unica=aviso.clave_unica)
    db.add(nuevo_aviso)
    db.commit()
    db.refresh(nuevo_aviso)
    db.close()
    return nuevo_aviso

@app.get("/avisos/")
def obtener_avisos():
    db = SessionLocal()
    avisos = db.query(Aviso).all()
    db.close()
    return avisos
