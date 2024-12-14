from passlib.context import CryptContext
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import APIRouter, Depends, HTTPException, Body, status, UploadFile, File, Form
from bson import ObjectId
from pymongo import ReturnDocument
from fastapi.responses import Response
from typing import List
from core.security import decode_access_token
from core.mongo import get_db
from models.alumno import AlumnoModel, Alumno, AlumnoCollection, UpdateAlumno, AlumnoCreate, AlumnoModelPass
from models.materia import MateriaSuper
from fastapi.security import OAuth2PasswordBearer
from api.routes.profesor import get_current_profesor
from helpers.helpers import upload_file, delete_file
from datetime import datetime
from typing import Optional


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://127.0.0.1:8000/api/v1/token")
router = APIRouter()

async def get_current_alumno(engine: AsyncIOMotorClient = Depends(get_db), token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    username = payload.get("sub")

    if not username:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    alumno = await engine.alumnos.find_one({"username": username})

    if not alumno:
        raise HTTPException(status_code=404, detail="Usuario no encontrado o no tienes permisos para esta funcionalidad")

    return AlumnoModel(**alumno)

@router.post(
    "/alumnos",
    response_description="Agregar un nuevo Alumno",
    response_model=AlumnoModel,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False,
    dependencies=[Depends(get_current_alumno)]
)
async def post_alumno(
    nombre: str = Form(...),
    apellido: str = Form(...),
    fecha_nacimiento: datetime = Form(...),
    direccion: str = Form(...),
    username: str = Form(...),
    hashed_password: str = Form(...),
    archivo: UploadFile = File(...),
    db: AsyncIOMotorClient = Depends(get_db)
    ):
    new_hashed_password = pwd_context.hash(hashed_password)
    
     # Obtener URL del archivo en S3
    file_url_response = await upload_file(file=archivo, bucket="alumnos-upiiz-sd", path="alumnos")
    
    if "url" in file_url_response:
        imagen = file_url_response["url"]
        alumno_aux = AlumnoModelPass(
            username=username,
            nombre=nombre,
            apellido=apellido,
            fecha_nacimiento=fecha_nacimiento,
            foto=imagen,
            direccion=direccion,
            hashed_password=new_hashed_password
        )
        new_alumno = await db.alumnos.insert_one({
            **alumno_aux.dict(exclude_unset=True),
        })
        created_alumno = await db.alumnos.find_one({"_id": new_alumno.inserted_id})
        return created_alumno
    else:
        raise HTTPException(status_code=500, detail="Error al subir la imagen")

@router.get(
    "/alumnos",
    response_description="Lista de todos los alumnos",
    response_model=AlumnoCollection,
    response_model_by_alias=False,
)
async def get_all_alumnos(db: AsyncIOMotorClient = Depends(get_db)):
    return AlumnoCollection(alumnos=await db.alumnos.find().to_list(1000))

@router.get(
    "/alumnos/{id}",
    response_description="Obtener un alumno",
    response_model=AlumnoModel,
    response_model_by_alias=False,
)
async def get_alumno_by_id(id: str, db: AsyncIOMotorClient = Depends(get_db)):
    if (
        alumno := await db.alumnos.find_one({"_id": ObjectId(id)})
    ) is not None:
        return alumno
    raise HTTPException(status_code=404, detail=f"Alumno {id} no encontrado")

@router.put(
    "/alumnos/{id}",
    response_description="Actualizar alumno",
    response_model=AlumnoModel,
    response_model_by_alias=False,
    dependencies=[Depends(get_current_alumno)],
)
async def update_alumno(
    id: str,
    nombre: str = Form(...),
    apellido: str = Form(...),
    fecha_nacimiento: datetime = Form(...),
    direccion: str = Form(...),
    username: str = Form(...),
    archivo: Optional[UploadFile] = None,
    db: AsyncIOMotorClient = Depends(get_db),
):
    # Verificar que el ID sea válido
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="ID no válido")

    # Buscar el alumno en la base de datos
    alumno = await db.alumnos.find_one({"_id": ObjectId(id)})
    if not alumno:
        raise HTTPException(status_code=404, detail="Alumno no encontrado")

    # Preparar campos para la actualización
    update_fields = {
        "nombre": nombre,
        "apellido": apellido,
        "fecha_nacimiento": fecha_nacimiento,
        "direccion": direccion,
        "username": username,
    }

    # Manejo del archivo (si se proporciona)
    if archivo:
        # Obtener la URL existente de la foto (si tiene)
        existing_file_url = alumno.get("foto")
        if existing_file_url:
            existing_file_name = existing_file_url.split('/')[-1]
            await delete_file("alumnos-upiiz-sd", "alumnos", existing_file_name)

        # Subir la nueva imagen
        file_url_response = await upload_file(file=archivo, bucket="alumnos-upiiz-sd", path="alumnos")
        if "url" in file_url_response:
            update_fields["foto"] = file_url_response["url"]
        else:
            raise HTTPException(status_code=500, detail="Error al subir la imagen")

    # Eliminar claves con valores nulos
    update_fields = {k: v for k, v in update_fields.items() if v is not None}

    # Actualizar el alumno en la base de datos
    updated_alumno = await db.alumnos.find_one_and_update(
        {"_id": ObjectId(id)},
        {"$set": update_fields},
        return_document=ReturnDocument.AFTER,
    )

    if updated_alumno:
        # # Convertir `_id` a cadena antes de devolver la respuesta
        # updated_alumno["_id"] = str(updated_alumno["_id"])
        # return AlumnoModel(**update_alumno)
        return updated_alumno
    else:
        raise HTTPException(status_code=500, detail="Error al actualizar el alumno")
    
@router.delete("/alumnos/{id}", response_description="Eliminar Alumno", dependencies=[Depends(get_current_profesor)])
async def delete_alumno(id: str, db: AsyncIOMotorClient = Depends(get_db)):
    # Validar que el ID sea válido
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="ID no válido")

    # Buscar el alumno para verificar si existe y obtener la URL de la imagen
    alumno = await db.alumnos.find_one({"_id": ObjectId(id)})
    if not alumno:
        raise HTTPException(status_code=404, detail=f"Alumno con ID {id} no encontrado")

    # Eliminar la imagen asociada del S3 si existe
    if "foto" in alumno and alumno["foto"]:
        existing_file_url = alumno["foto"]
        existing_file_name = existing_file_url.split('/')[-1]
        await delete_file(bucket="alumnos-upiiz-sd", path="alumnos", file_name=existing_file_name)

    # Intentar eliminar el documento del alumno
    delete_result = await db.alumnos.delete_one({"_id": ObjectId(id)})
    if delete_result.deleted_count == 1:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    # Error inesperado (no debería ocurrir después de las validaciones)
    raise HTTPException(status_code=500, detail="Error al intentar eliminar al alumno")

@router.post(
    "/alumnos/{id_alumno}/inscribir",
    response_description="Inscribir alumno a una materia",
    response_model=MateriaSuper,
    status_code=status.HTTP_201_CREATED,
    #dependencies=[Depends(get_current_alumno)]  # Requiere autenticación
)
async def inscribir_alumno_a_materia(
    id_alumno: str,
    id_materia: str = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_db)
):
    # Verifica que el alumno exista
    alumno = await db.alumnos.find_one({"_id": ObjectId(id_alumno)})
    if not alumno:
        raise HTTPException(status_code=404, detail="Alumno no encontrado")

    # Verifica que la materia exista
    materia = await db.materias.find_one({"_id": ObjectId(id_materia)})
    if not materia:
        raise HTTPException(status_code=404, detail="Materia no encontrada")

    # Agrega el ID del alumno al campo `alumnos` en la materia
    if "alumnos" not in materia or not isinstance(materia["alumnos"], list):
        materia["alumnos"] = []

    if ObjectId(id_alumno) not in materia["alumnos"]:
        materia["alumnos"].append(ObjectId(id_alumno))
        await db.materias.update_one(
            {"_id": ObjectId(id_materia)},
            {"$set": {"alumnos": materia["alumnos"]}}
        )

    get_materia = await db.materias.find_one({"_id": ObjectId(id_materia)})
    return get_materia

