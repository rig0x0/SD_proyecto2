from pydantic import BaseModel, Field, BeforeValidator
from typing import Optional, List
from datetime import datetime
from typing_extensions import Annotated

PyObjectId = Annotated[str, BeforeValidator(str)]

class MateriaSuper(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    nombre: str = Field(...)
    descripcion: str = Field(...)
    id_profesor: PyObjectId = Field(...)
    alumnos: List[PyObjectId]
    
# Modelo para representar la Materia
class MateriaModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    nombre: str = Field(...)
    descripcion: str = Field(...)
    

# Para crear una nueva Materia (sin id)
class Materia(MateriaModel):
    pass

# Para actualizar una Materia (pueden ser campos opcionales)
class UpdateMateria(BaseModel):
    nombre: Optional[str] = Field(None)
    descripcion: Optional[str] = Field(None)

class AsignarProfesor(MateriaSuper):
    id_profesor: PyObjectId = Field(...)
    
class AsignarAlumno(MateriaSuper):
    alumnos: Optional[List] = Field(...)
    

# Colección de Materias
class MateriaCollection(BaseModel):
    materias: List[MateriaSuper]
