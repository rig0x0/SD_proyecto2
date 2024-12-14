
# API de Gestión Escolar UPIIZ

## Alumnos
- Felipe Martínez Reyna
- Gerardo Issac Luna Rodarte
- Cristopher Isaí Velázquez Medina
- Rodrigo Emiliano Maldonado de la Cruz
- Rogelio Bustamante Ibarra

## Descripción del Proyecto

Este proyecto es una API diseñada para gestionar la informacion de los estudiantes, profesores, materias y calificaciones en una escuela. Proporciona una API RESTful construida con **FastAPI**, almacena los datos en **MongoDB** y utiliza **AWS S3** para almacenar las fotos de los estudiantes.

### Características
- **Alumnos**:
  - Crear, leer, actualizar y eliminar registros de estudiantes.
  - Cada alumno tiene un ID unico, nombre, apellido, fecha de nacimiento, dirección y foto.
  - Las fotos de los estudiantes se almacenan en **AWS S3**.

- **Profesores**:
  - Crear, leer, actualizar y eliminar registros de profesores.
  - Cada profesor tiene un ID unico, nombre, apellido, fecha de nacimiento, dirección y especialidad.

- **Materias**:
  - Crear, leer, actualizar y eliminar registros de materias.
  - Cada materia tiene un ID unico, nombre y descripcion.

- **Asignación de materias a profesores**:
  - Un profesor puede ser asignado a varias materias.

- **Inscripción de alumnos a materias**:
  - Un alumno puede estar inscrito en varias materias.

- **Calificaciones**:
  - Los profesores pueden asignar calificaciones a los estudiantes en materias espec�ficas.
  - Las calificaciones están asociadas a los estudiantes y las materias.

- **Autenticación y Autorización**:
  - La API utiliza tokens JWT para asegurar que solo los usuarios autorizados puedan acceder o modificar los datos.

### Requisitos
- Python 3.9 o superior
- MongoDB (nombre de la base de datos: ESCUELA, colecciones: alumnos,profesores,materias,calificaciones)
- Cuenta de AWS S3 para almacenar las fotos de los estudiantes(modificar bucketname y crear carpetas /imagenes/alumnos)
- Bibliotecas de Python necesarias: passlib, PyJWT (principalmente)

### Explicacion de puntos a destacar
## Autenticación y Autorización
La API implementa autenticación mediante tokens JWT (JSON Web Tokens). Los usuarios deben iniciar sesión con sus credenciales, 
y si son válidas, se les asigna un token de acceso. Para acceder a rutas protegidas (como crear o actualizar registros), 
el token debe ser enviado en el encabezado de la solicitud. La API valida el token para asegurar que solo los usuarios autorizados 
puedan realizar ciertas acciones.

## Manejo de Archivos en AWS S3
Las fotos de los estudiantes se almacenan en **AWS S3** en lugar de la base de datos MongoDB. Al subir una foto, el archivo 
se guarda de manera eficiente en S3, mejorando el rendimiento y la escalabilidad del sistema.

## Validación de Datos
La API utiliza **Pydantic** para validar los datos de las solicitudes. Esto asegura que los datos, como el nombre, apellido y 
fecha de nacimiento de los alumnos, cumplan con las restricciones definidas. Si los datos no son v�lidos, la API devuelve un error, 
garantizando la consistencia y calidad de la información almacenada.

### Ejecucion
```bash
FastApi dev main.py
```
### Documentacion de la API
La documentacion interactiva de la API esta disponible en Swagger en el siguiente enlace:
```arduino
http://127.0.0.1:8000/docs
```
### Ejemplos de uso
## Crear un Alumno
Esta solicitud esta restringida para profesores que se hayan autorizado
-Metodo: POST
-Endopoint: /api/v1/alumnos
-Cuerpo:
```json
{
  "nombre": "Juan",
  "apellido": "Perez",
  "fecha_nacimiento": "2000-01-01T00:00:00",
  "direccion": "Calle Ficticia 123",
  "foto": "url_de_la_foto"
}
```

## Asignar Materia a un Profesor
Esta solicitud esta restringida para profesores que se hayan autorizado
-Metodo: POST
-Endopoint: /api/v1/materias/asignar
-Cuerpo:
```json
{
  "id_profesor": "id_del_profesor",
  "id_materia": "id_de_materia"
}
```

## Registrar calificacion
Esta solicitud esta restringida para profesores que se hayan autorizado
-Metodo: POST
-Endopoint: /api/v1/calificaciones
-Cuerpo:
```json
{
  "id_alumno": "id_del_alumno",
  "id_materia": "id_de_materia",
  "calificacion": 8.5
}
```

### Consideraciones
-Limitaciones de AWS S3: AWS S3 tiene límites en la cantidad de solicitudes y el tamaño de los archivos. Asegúrate de tener configurada 
una cuenta con suficientes recursos.

-Manejo de errores: Si la API encuentra errores durante el procesamiento de las solicitudes (por ejemplo, si la base de datos
 no está disponible o el archivo no se puede cargar a S3), se devolverán mensajes de error adecuados con el código de estado HTTP correspondiente.

