""" Probar mapade tokens PostGrade 
"""
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy import create_engine, Column, Integer, Float, String, ForeignKey, select, Select, DateTime
from sqlalchemy.orm import declarative_base, relationship, joinedload
from sqlalchemy.schema import PrimaryKeyConstraint
from typing import Annotated, Optional
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
import cloudinary
import cloudinary.uploader
import os
import secrets

cloudinary.config(
  cloud_name='dnlios4ua',
  api_key='747777351831491',
  api_secret='mvqCvHtSJYQHgKhtEwAfsHw93FI',
  secure=True
)
# Configuración desde variables de entorno
##cloudinary.config(
   ## cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
   ## api_key=os.environ.get("CLOUDINARY_API_KEY"),
   ## api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
   ## secure=True
##)

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
]
###import models
#from sqlalchemy.pool import SingletonThreadPool
#engine = create_engine('sqlite:///mydb.db',
#                poolclass=SingletonThreadPool)

#DATABASE_URL = "postgresql://usuario:contraseña@host:puerto/nombre_db"
DATABASE_URL = "postgresql://laburantes_db_user:mtNUViyTddNAbZhAVZP6R23G9k0BFcJY@dpg-d1m3kqa4d50c738f4a7g-a:5432/laburantes_db"
engine = create_engine(DATABASE_URL)



# Make the DeclarativeMeta
Base = declarative_base()

# Declare Classes / Tables
#nuevos############### 28 / 3
class Usuarios_Servicios_Trabajadores(Base):
    __tablename__ = 'usuarios_servicios_trabajadores'
    ##id = Column(Integer, primary_key=True)
    # clave compuesta por el servicio + el trabajador
    #SQLite does not support autoincrement for composite primary keys
    usuario_id = Column ('usuario_id', ForeignKey('usuarios.id'), primary_key=True)
    servicio_trabajador_id = Column('servicio_trabajador_id', ForeignKey('servicios_trabajadores.id'), primary_key=True)


###############  
# Modelo SQLAlchemy para la tabla tracking
class Tracking(Base):
    __tablename__ = 'tracking'
    id = Column(Integer, primary_key=True, autoincrement=True)
    fecha_hora = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    latitud = Column(Float, nullable=False)
    longitud = Column(Float, nullable=False)
    id_android = Column(String, nullable=False)

# Modelo Pydantic para recibir datos desde el frontend
class TrackingCreate(BaseModel):
    latitud: float
    longitud: float
    id_android: str
###############  



class Servicios_Trabajadores(Base):
    __tablename__ = 'servicios_trabajadores'
    id = Column(Integer, primary_key=True)
    # clave compuesta por el servicio + el trabajador
    #SQLite does not support autoincrement for composite primary keys
    servicio_id = Column ('servicio_id', ForeignKey('servicios.id'), primary_key=True)
    trabajador_id = Column('trabajador_id', ForeignKey('trabajadores.id'), primary_key=True)
    precioxhora = Column ('precioxhora',Integer)
     #nuevos############### 28 / 3
    usuarios = relationship("Usuario", secondary="usuarios_servicios_trabajadores", back_populates='servicios_trabajadores')  
    #trabajadores = relationship("Trabajador", secondary="servicios", back_populates='servicios_trabajadores')  

    ###############       
class Servicios_TrabajadoresUpdate(SQLModel):
    precioxhora: int | None = None
      

class Servicio(Base):
    __tablename__ = 'servicios'
    id = Column(Integer, primary_key=True)
    titulo = Column(String, nullable=False)
    trabajadores = relationship("Trabajador", secondary="servicios_trabajadores", back_populates='servicios')

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
    token = Column(String, unique=True, index=True)
    servicios = relationship("Servicio", secondary="servicios_trabajadores", back_populates='trabajadores')

    #nuevos############### 19 / 6
class Opinion(Base):
    __tablename__ = 'opiniones'
    id = Column(Integer, primary_key=True, index=True)
    #trabajador_id = Column(Integer, ForeignKey("trabajadores.id"), nullable=False)
    trabajador_id = Column(Integer)

    comentario = Column(String, nullable=False)
    calificacion = Column(Integer, nullable=False)  # Valor de 1 a 5, por ejemplo
    fecha = Column(DateTime, default=datetime.now(timezone.utc))
    #### para ver opiniones es lo que sigue



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

#nuevos############### 28 / 3

class TrabajadorUpdate(SQLModel):
    #id: int | None = None
    #nombre: str | None = None
    #dni: str | None = None
    # los campos anteriores no se pueden actualizar
    correoElec: str | None = None
    direccion: str | None = None
    localidad: str | None = None
    latitud: float | None = None
    longitud: float | None = None
    wsapp: str | None = None
    penales: str | None = None

###

class UsuarioBase(SQLModel):
    nombre: str = Field(index=True)

class TrabajadorBase(SQLModel):
    nombre: str = Field(index=True)


class ServicioTrabajadorBase(SQLModel):
    precioxhora: int = Field(index=True)


class TrabajadorPublic(TrabajadorBase):
    id: int
##### nuevo
class ServicioTrabajadorPublic(ServicioTrabajadorBase):
    id: int

##############################  
    
# Create the tables in the database
Base.metadata.create_all(engine)

# Insert data, en la práctica estos valores deberían pasarse como parámetros
from sqlalchemy.orm import Session
#aqui estaba la inicializacion
import json
from typing import List
from pydantic import BaseModel, constr
from fastapi.encoders import jsonable_encoder

class OpinionCreate(BaseModel):
    comentario: str
    calificacion: int
    
class OpinionOut(BaseModel):
    comentario: str
    calificacion: int

    class Config:
        orm_mode = True


class UsuarioServicioTrabajadorBase(BaseModel):
    usuario_id: int
    servicio_trabajador_id: int
    
class ServicioTrabajadorBase(BaseModel):
    servicio_id: int
    trabajador_id: int
    #precioxhora: int

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

class UsuarioBase(BaseModel):
    nombre: str
    dni: str
    correoElec: str
    direccion: str
    localidad: str
    wsapp: str
  
class Config:
        orm_mode = True

class ServicioBase(BaseModel):
    #id: int
    titulo: str
    
class Config:
        orm_mode = True

class ServicioSchema(ServicioBase):
    trabajadores: List[TrabajadorBase]

class TrabajadorSchema(TrabajadorBase):
    servicios: List[ServicioBase]
#####################################

class ServicioTrabajadorSchema(ServicioTrabajadorBase):
    serviciostrabajadores: List[ServicioTrabajadorBase]
#####################################
def get_session():
    with Session(engine) as session:
        yield session
#####################################
from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from fastapi import Query
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

SessionDep = Annotated[Session, Depends(get_session)]
app = FastAPI()
# Ruta absoluta a la carpeta de fotos
app.mount("/static", StaticFiles(directory="fotos"), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = Session(bind=engine)
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
@app.post("/cargar_oficios/")
def cargar_oficios(db: Session = Depends(get_db)):
    oficios = [
        'Albañil','Informático','Taxi','Mozo','Programador Web','Programador Front End','Programador Back End','Vendedor' ,'Vendedor Ambulante' ,'Ayudante de Cocina' ,'Chapista' ,'Membranas', 'Zinguero','Empleada Doméstica' ,'Enfermera - Enfermero', 'Perforaciones','Taxista','Electricista','Electricista del Automotor' ,'Plomero', 'Gasista matriculado', 'Carpintero', 'Pintor',
        'Cerrajero', 'Techista', 'Colocador de cerámicos', 'Colocador de durlock', 'Soldador',
        'Mecánico automotor','Delyvery','Remisse', 'Mecánico de motos', 'Reparador de electrodomésticos', 'Herrero',
        'Jardinero', 'Podador', 'Cuidadores de adultos mayores', 'Niñera', 'Maestra particular',
        'Cocinero a domicilio', 'Delivery con moto', 'Mudanzas y fletes', 'Peluquero/a',
        'Manicuría y pedicuría', 'Estética y depilación', 'Masajista', 'Personal trainer',
        'Entrenador deportivo', 'Profesor de música', 'Profesor de inglés','Profesor de Matemáticas' ,' Profesor de Gimnasia','Profesor de Danzas' ,'Profesor de Música' ,'Clases de apoyo escolar',
        'Diseñador gráfico', 'Diseñador web', 'Fotógrafo', 'Videógrafo', 'Community manager',
        'Desarrollador de software', 'Técnico en computación', 'Armado y reparación de PC',
        'Instalador de cámaras de seguridad', 'Instalador de redes', 'Servicio de limpieza',
        'Limpieza de vidrios', 'Limpieza final de obra', 'Cuidado de mascotas', 'Paseador de perros',
        'Adiestrador canino', 'Yesero', 'Parquero', 'Servicio de catering', 'DJ para eventos',
        'Animador de fiestas infantiles', 'Mozo para eventos', 'Bartender', 'Diseño de interiores',
        'Montador de muebles', 'Costurera', 'Modista', 'Sastre', 'Tapicero', 'Tornero',
        'Gomería móvil', 'Lavado de autos a domicilio', 'Reparación de bicicletas',
        'Maquinista rural', 'Peón rural', 'Cuidador de campo', 'Apicultor', 'Viverista',
        'Cortador de leña', 'Operario de maquinaria pesada', 'Zanellero', 'Herrador','Chofer', 'Talabertero-a'
        'Pintura artística', 'Diseño de tatuajes', 'Tatuador', 'Estilista canino','Constructor', 'Maestro Mayor de Obras'
    ]

    for titulo in oficios:
        db.add(Servicio(titulo=titulo))
    db.commit()
    return {"mensaje": f"Se insertaron {len(oficios)} oficios"}


#@app.post("/registro/", status_code=status.HTTP_201_CREATED)
############### podificado por gpt
#async def crear_registro_Trabajador(registro: TrabajadorBase, db: db_dependency):
#   db_registro = Trabajador(**registro.dict())
#    db.add(db_registro)
#    db.commit()
#    db.refresh(db_registro)
#    return {"mensaje": "Registro exitoso", "id": db_registro.id}

# Crear
@app.post("/registro/")
def crear_trabajador(trabajador: TrabajadorBase, db: Session = Depends(get_db)):
    token = secrets.token_hex(16)
    nuevo = Trabajador(**trabajador.dict(), token=token)
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return {"id": nuevo.id, "token": token}

####################################################
@app.get("/Servicios_React/")
async def Servicios(db: Session = Depends(get_db)):

    # Cuento los registros de servicios_trabajadores existentes
    db_servicios = db.query(Servicio.id).all()
    tags = [row[0] for row in db_servicios] 
    # Selecciono las columnas a listar: Joint de las 3 tablas de 
    db_stmt = select(Servicio.titulo).select_from (Servicio) 
    
    # ejecuto la consulta
    result = db.execute(db_stmt)
    # asigno los valores a los 4 campos seleccionados
    servicio =  [row[0] for row in result]

    a=''
    #genero tantos strings al front como registros existen de servicios_trabajadores
    for i in range(0, len(tags)):
        a = a +str(tags[i])+' '+str(servicio[i])+'---'
    a = a.split(sep='---', maxsplit=-1)
    a.pop()
    a = [
    #{int(linea.split(' ', 1)[0]), linea.split(' ', 1)[1]}
    {"id": int(linea.split(' ', 1)[0]), "nombre": linea.split(' ', 1)[1]}
    
    for linea in a]
    return {'RegLog': a }
##################################################
@app.post("/Relacionar_Trabajador_Servicio/", status_code=201)
async def crear_Relacion_Trabajador_Servicio(registro: ServicioTrabajadorBase, db: db_dependency):
    db_registro = Servicios_Trabajadores(**registro.dict())
    db_registro.id = int(str(db_registro.servicio_id) + str(db_registro.trabajador_id))
    db.add(db_registro)
    db.commit()
    return {"mensaje": "Relación creada correctamente"}
##################################################
# Listar
@app.get("/Listo_trabajadoresPorServicio/{titulo_servicio}")
def listar_trabajadores_por_servicio(titulo_servicio: str, db: Session = Depends(get_db)):
    consulta = (
        db.query(
            Servicio.titulo, 
            Trabajador.id, 
            Trabajador.nombre, 
            Trabajador.penales, 
            Trabajador.foto, 
            Trabajador.wsapp, 
            Trabajador.latitud, 
            Trabajador.longitud,
            Trabajador.token  # 👈 agregado token
        )
        .join(Servicios_Trabajadores, Servicio.id == Servicios_Trabajadores.servicio_id)
        .join(Trabajador, Trabajador.id == Servicios_Trabajadores.trabajador_id)
        .filter(Servicio.titulo == titulo_servicio)
        .all()
    )
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
            "token": row[8]  # 👈 incluimos token en el JSON
        }
        for row in consulta
    ]
    return {"trabajadores": resultado}

#
####################################################
@app.get("/Servicios/")
async def Servicios(db: Session = Depends(get_db)):

    # Cuento los registros de servicios_trabajadores existentes
    db_servicios = db.query(Servicio.id).all()
    tags = [row[0] for row in db_servicios] 
    # Selecciono las columnas a listar: Joint de las 3 tablas de 
    db_stmt = select(Servicio.titulo).select_from (Servicio) 
    
    # ejecuto la consulta
    result = db.execute(db_stmt)
    # asigno los valores a los 4 campos seleccionados
    servicio =  [row[0] for row in result]

    a=''
    #genero tantos strings al front como registros existen de servicios_trabajadores
    for i in range(0, len(tags)):
        a = a +str(servicio[i])+'---'
    a = a.split(sep='---', maxsplit=-1)
    a.pop()
    return {'RegLog': a }
####################################################
@app.get("/Servicios/{id}", response_model=ServicioSchema)
async def get_servicio(id: int, db: Session = Depends(get_db)):
    db_servicio = db.query(Servicio).options(joinedload(Servicio.trabajadores)).\
        where(Servicio.id == id).one()
    return db_servicio
####################################################
@app.get("/Trabajadores/")
async def get_trabajadores(db: Session = Depends(get_db)):
    db_trabajadores = db.query(Trabajador.id).all()
    #db_authors = db.query(Author).options(joinedload(Author.books)).all()
    tags1 = [row[0] for row in db_trabajadores] 
    db_trabajadoresname = db.query(Trabajador.nombre).all()
    tat = [row[0] for row in db_trabajadoresname]
    #Ahora busco los trabajadores
    mi_lista = []
    users=''
    for i in range(0, len(tags1)):
       
       #users = users + str(db.query(Trabajador).get({"id": tags[i]}).id) + ' ' + db.query(Trabajador).get({"id": tags[i]}).nombre + '---'
       users = users +str([ s.id for s in db_trabajadores if s.id == tags1[i]]) + '-' + str([ tat[s.id-1] for s in db_trabajadores if s.id == tags1[i]]) + '---'
    users = users.split(sep='---', maxsplit=-1)
    #return {'Clave y Nombrs de Trabajador': users}
    return users
####################################################

@app.get("/Trabajadores/{id}", response_model=TrabajadorSchema)
async def get_trabajador(id: int, db: Session = Depends(get_db)):
    db_trabajador = db.query(Trabajador).options(joinedload(Trabajador.servicios)).\
        where(Trabajador.id == id).one()
    return db_trabajador
####################################################
@app.get("/opiniones_por_trabajador/{trabajador_id}")
def opiniones_por_trabajador(trabajador_id: int, db: Session = Depends(get_db)):
    opiniones = db.query(Opinion).filter(Opinion.trabajador_id == trabajador_id).order_by(Opinion.id.desc()).all()
    return opiniones
####################################################
@app.post("/opiniones/{param}")
def crear_opinion(param: int, opinion: OpinionCreate, db: Session = Depends(get_db)):
    nueva_opinion = Opinion(
        trabajador_id=param,
        comentario=opinion.comentario,
        calificacion=opinion.calificacion,
    )
    db.add(nueva_opinion)
    db.commit()
    db.refresh(nueva_opinion)
    return {"mensaje": "Opinión registrada con éxito", "id": nueva_opinion.id}
###########F I N BackEnd #########################################
@app.post("/tracking/", status_code=status.HTTP_201_CREATED)
async def crear_tracking(tracking: TrackingCreate, db: Session = Depends(get_db)):
    nuevo_tracking = Tracking(
        latitud=tracking.latitud,
        longitud=tracking.longitud,
        id_android=tracking.id_android,
        fecha_hora=datetime.now(timezone.utc)  # Fecha calculada en backend
    )
    db.add(nuevo_tracking)
    db.commit()
    db.refresh(nuevo_tracking)
    return {"mensaje": "Tracking registrado", "id": nuevo_tracking.id}
###########F I N BackEnd #########################################from pydantic import BaseModel


from pydantic import BaseModel
class ActualizarDescripcion(BaseModel):
    descripcion: str
    token: str
# Editar
from fastapi import Body

@app.patch("/trabajadores/{idt}")
def actualizar_descripcion(
    idt: int,
    payload: ActualizarDescripcion = Body(...),
    db: Session = Depends(get_db)
):
    trabajador = db.query(Trabajador).filter(
        Trabajador.id == idt,
        Trabajador.token == payload.token
    ).first()

    if not trabajador:
        raise HTTPException(status_code=403, detail="Token inválido o trabajador no encontrado")

    # ⚠️ Guardar en la columna correcta
    trabajador.penales = payload.descripcion
    db.commit()
    db.refresh(trabajador)

    return {"msg": "Descripción actualizada", "penales": trabajador.penales}







@app.get("/ping")
def ping():
    print("🔔 PINGA recibido")
    return {"Pinga ok": True}
####################
from fastapi import FastAPI, HTTPException, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

class FotoUpdate(BaseModel):
    nueva_foto_url: str
    vieja_foto_url: str | None = None  # opcional, para borrar en Cloudinary

@app.put("/trabajadores/{trabajador_id}/foto")
def update_foto(
    *,
    session: Session = Depends(get_session),
    trabajador_id: int,
    payload: FotoUpdate
):
    db_trabajador = session.get(Trabajador, trabajador_id)
    if not db_trabajador:
        raise HTTPException(status_code=404, detail="Trabajador no encontrado")

    # Actualizamos la foto
    db_trabajador.foto = payload.nueva_foto_url
    session.add(db_trabajador)
    session.commit()
    session.refresh(db_trabajador)

    # Intentamos borrar la foto vieja en Cloudinary si viene
    if payload.vieja_foto_url:
        try:
            import cloudinary.uploader
            public_id = payload.vieja_foto_url.split("/")[-1].split(".")[0]
            cloudinary.uploader.destroy(public_id)
        except Exception as e:
            print(f"⚠️ No se pudo eliminar la foto vieja: {e}")

    return {"msg": "Foto actualizada correctamente", "trabajador_id": trabajador_id, "nueva_foto": db_trabajador.foto}


####################
from fastapi import Body

class DeleteFotoRequest(BaseModel):
    foto_url: str

@app.delete("/trabajadores/foto")
def delete_foto(
    payload: DeleteFotoRequest = Body(...)
):
    try:
        import cloudinary.uploader
        public_id = payload.foto_url.split("/")[-1].split(".")[0]
        result = cloudinary.uploader.destroy(public_id)
        if result.get("result") not in ("ok", "not_found"):
            raise HTTPException(status_code=400, detail=f"Error eliminando foto: {result}")
        return {"msg": "Foto eliminada correctamente", "public_id": public_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error eliminando foto: {e}")
####################
# Borrar
cloudinary.config(
  cloud_name='dnlios4ua',
  api_key='747777351831491',
  api_secret='mvqCvHtSJYQHgKhtEwAfsHw93FI',
  secure=True
)
from pydantic import BaseModel

class TokenPayload(BaseModel):
    token: str
@app.delete("/trabajadores/{idt}")
def eliminar_trabajador(
    idt: int,
    payload: TokenPayload = Body(...),
    db: Session = Depends(get_db)
):
    # Validar token
    trabajador = db.query(Trabajador).filter(
        Trabajador.id == idt,
        Trabajador.token == payload.token
    ).first()

    if not trabajador:
        raise HTTPException(status_code=403, detail="Token inválido o trabajador no encontrado")

    # Eliminar foto de Cloudinary si existe
    if trabajador.foto:
        try:
            cloudinary.uploader.destroy(trabajador.foto)
        except Exception as e:
            print(f"⚠️ Error eliminando foto en Cloudinary: {e}")

    # Eliminar opiniones asociadas
    db.query(Opinion).filter(Opinion.trabajador_id == idt).delete()

    # Eliminar filas en servicio_trabajadores
    db.query(Servicios_Trabajadores).filter(
        Servicios_Trabajadores.trabajador_id == idt
    ).delete()

    # Eliminar trabajador
    db.delete(trabajador)
    db.commit()

    return {"msg": "Trabajador eliminado correctamente"}
#############################################################
#@app.get("/login_unico/{trabajador_id}/{token}", response_model=TrabajadorSchema)
#def login_unico(trabajador_id: int, token: str, db: Session = Depends(get_db)):
@app.get("/login_unico/{dni}", response_model=TrabajadorSchema)
def login_unico(dni: str, db: Session = Depends(get_db)):
    trabajador = db.query(Trabajador).filter(
        #Trabajador.id == trabajador_id,
        ##Trabajador.token == token
        Trabajador.dni == dni
    ).first()
    if not trabajador:
        raise HTTPException(status_code=404, detail="Trabajador no encontrado o token inválido")
    return trabajador


####################################################



   
