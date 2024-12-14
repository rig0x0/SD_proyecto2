from fastapi import Depends, HTTPException, status
import boto3
from botocore.exceptions import ClientError
import uuid
import logging
import os
from fastapi import File, UploadFile
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from models.profesor import Profesor
from core.mongo import get_db

async def get_profesor_by_username(username: str, db: AsyncIOMotorClient = Depends(get_db)):
    try:
        if (
          profesor := await db.profesores.find_one({"username": username})
        ) is not None:
          return profesor
        # raise HTTPException(status_code=404, detail=f"Profesor{id} no encontrado")
        return None
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
      
async def get_alumno_by_username(username: str, db: AsyncIOMotorClient = Depends(get_db)):
    try:
        if (
         alumno := await db.alumnos.find_one({"username": username})
        ) is not None:
          return alumno
        return None
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
async def upload_file(file: UploadFile, bucket: str, path: str):
    
    s3_client = boto3.client('s3')

    content = await file.read()
    
    # Generar un nombre único para el archivo
    file_extension = file.filename.split('.')[-1]
    unique_file_name = f"{uuid.uuid4()}.{file_extension}"
    
    # Guardar la imagen temporalmente en el servidor
    temp_file_path = f"temp/{unique_file_name}"
    with open(temp_file_path, "wb") as f:
        f.write(content)

    object_name = f"imagenes/{path}/{unique_file_name}"

    try:
        # Subir el archivo al bucket de S3
        s3_client.upload_file(temp_file_path, bucket, object_name)

        # Crear la URL pública para acceder al archivo en S3
        file_url = f"https://{bucket}.s3.amazonaws.com/{object_name}"

        # Eliminar el archivo local después de la subida
        os.remove(temp_file_path)
        
        return {"url": file_url}
    except ClientError as e:
        logging.error(e)
        return JSONResponse(status_code=500, content={"error": "Error subiendo el archivo a S3"})
    

async def delete_file(bucket: str, path: str, file_name: str):
    s3_client = boto3.client('s3')

    object_name = f"imagenes/{path}/{file_name}"

    try:
        # Eliminar el archivo del bucket de S3
        s3_client.delete_object(Bucket=bucket, Key=object_name)
        return True
    except ClientError as e:
        logging.error(e)
        return JSONResponse(status_code=500, content={"error": "Error eliminando el archivo en S3"})
