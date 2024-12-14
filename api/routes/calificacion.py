from fastapi import APIRouter, Depends, HTTPException, Body, status
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from pymongo import ReturnDocument
from fastapi.responses import Response
from api.routes.profesor import get_current_profesor
from models.calificacion import CalificacionModel, Calificacion, CalificacionCollection, UpdateCalificacion
from core.mongo import get_db
from core.security import decode_access_token
from fastapi.security import OAuth2PasswordBearer


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://127.0.0.1:8000/api/v1/token")
router = APIRouter()

@router.post(
    "/calificaciones",
    response_description="Registrar nueva calificación",
    response_model=CalificacionModel,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_profesor)]
)
async def post_calificacion(calificacion: Calificacion = Body(...), db: AsyncIOMotorClient = Depends(get_db)):
    # Verificar que el alumno exista
    if not await db.alumnos.find_one({"_id": ObjectId(calificacion.id_alumno)}):
        raise HTTPException(status_code=404, detail="Alumno no encontrado")
    # Verificar que la materia exista
    if not await db.materias.find_one({"_id": ObjectId(calificacion.id_materia)}):
        raise HTTPException(status_code=404, detail="Materia no encontrada")
    new_calificacion = await db.calificaciones.insert_one({
        **calificacion.dict(exclude_unset=True),
    })
    created_calificacion = await db.calificaciones.find_one({"_id": new_calificacion.inserted_id})
    return created_calificacion

@router.get(
    "/calificaciones",
    response_description="Lista de todos las calificaciones",
    response_model=CalificacionCollection,
    response_model_by_alias=False,
)
async def get_all_calificaciones(db: AsyncIOMotorClient = Depends(get_db)):
    return CalificacionCollection(calificaciones=await db.calificaciones.find().to_list(1000))

@router.get(
    "/calificaciones/{id}",
    response_description="Obtener una calificacion",
    response_model=CalificacionModel,
)
async def get_calificacion_by_id(id: str, db: AsyncIOMotorClient = Depends(get_db)):
    if (calificacion := await db.calificaciones.find_one({"_id": ObjectId(id)})) is not None:
        return calificacion
    raise HTTPException(status_code=404, detail=f"Calificacion {id} no encontrada")

@router.get(
    "/calificaciones/{id_alumno}",
    response_description="Listar calificaciones por alumno",
    response_model=CalificacionCollection,
)
async def get_calificaciones_by_alumno(id_alumno: str, db: AsyncIOMotorClient = Depends(get_db)):
    # Verifica que el alumno exista
    if not await db.alumnos.find_one({"_id": ObjectId(id_alumno)}):
         raise HTTPException(status_code=404, detail="Alumno no encontrado")
    
    calificaciones = await db.calificaciones.find({"id_alumno": ObjectId(id_alumno)}).to_list(1000)
    print(calificaciones)
    return CalificacionCollection(calificaciones=calificaciones)

@router.put(
    "/calificaciones/{id}",
    response_description="Actualizar calificacion",
    response_model=CalificacionModel,
    dependencies=[Depends(get_current_profesor)]
)
async def update_calificacion(id: str, calificacion: UpdateCalificacion = Body(...), db: AsyncIOMotorClient = Depends(get_db)):
    calificacion_data = {
        k: v for k, v in calificacion.dict(exclude_unset=True).items() if v is not None
    }
    if len(calificacion_data) >= 1:
        update_result = await db.calificaciones.find_one_and_update(
            {"_id": ObjectId(id)},
            {"$set": calificacion_data},
            return_document=ReturnDocument.AFTER,
        )
        if update_result is not None:
            return update_result
        else:
            raise HTTPException(status_code=404, detail=f"Calificacion {id} no encontrada")
    raise HTTPException(status_code=400, detail="No se proporcionaron datos para actualizar")


@router.delete("/calificaciones/{id}", response_description="Eliminar Calificacion", dependencies=[Depends(get_current_profesor)])
async def delete_calificacion(id: str, db: AsyncIOMotorClient = Depends(get_db)):
    delete_result = await db.calificaciones.delete_one({"_id": ObjectId(id)})
    if delete_result.deleted_count == 1:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    raise HTTPException(status_code=404, detail=f"Calificacion {id} no encontrada")