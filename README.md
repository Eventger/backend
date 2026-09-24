# Eventger backend

API REST construida con Django y Django REST Framework para gestionar eventos y
subtareas logísticas. Durante Sprint 1 utiliza el usuario compartido `demo`; la
autenticación y el aislamiento por usuario corresponden a un sprint posterior.

## Requisitos

- Python 3.12.
- PostgreSQL.
- Una base de datos disponible mediante `DATABASE_URL`.

## Desarrollo local

Crear el entorno e instalar dependencias:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Crear `.env` con los valores locales:

```dotenv
SECRET_KEY=una-clave-local-larga-y-aleatoria
DEBUG=true
DATABASE_URL=postgresql://usuario:contrasena@127.0.0.1:5432/eventger
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

Preparar la base de datos:

```bash
python manage.py migrate
python manage.py bootstrap_demo
```

`bootstrap_demo` crea de forma idempotente el usuario `demo` y el catálogo inicial de
tipos de evento. Puede ejecutarse varias veces sin duplicar registros.

Comprobar y ejecutar:

```bash
python manage.py check
python manage.py test
python manage.py runserver
```

Direcciones locales:

- API: http://127.0.0.1:8000/
- Health check: http://127.0.0.1:8000/health/
- Swagger: http://127.0.0.1:8000/api/docs/
- Esquema OpenAPI: http://127.0.0.1:8000/api/schema/

## Endpoints

| Método | Ruta | Descripción |
| --- | --- | --- |
| GET, POST | `/events/` | Listar y crear eventos del usuario demo |
| GET, PUT, PATCH, DELETE | `/events/{id}/` | Consultar, actualizar o eliminar un evento |
| GET | `/event-types/` | Listar tipos de evento |
| GET, POST | `/events/{event_id}/subtasks/` | Listar o crear subtareas dentro de un evento |
| GET | `/subtasks/` | Listar subtareas del usuario demo |
| GET, PUT, PATCH, DELETE | `/subtasks/{id}/` | Consultar, actualizar o eliminar una subtarea |

`POST /subtasks/` no está habilitado. Toda subtarea debe crearse mediante la ruta
del evento al que pertenece.

## Contrato de respuestas

Las respuestas exitosas utilizan `success` y `data`; las operaciones de escritura
pueden incluir `message`:

```json
{
  "success": true,
  "message": "Evento creado correctamente.",
  "data": {}
}
```

Los errores de la API DRF utilizan un formato uniforme:

```json
{
  "success": false,
  "message": "Los datos enviados no son válidos.",
  "errors": {
    "name": ["Este campo es requerido."]
  }
}
```

## Pruebas y validación

La validación oficial utiliza PostgreSQL aislado y `config.settings_test`. Consulta
[docs/validacion-backend.md](docs/validacion-backend.md) para levantar la base de
pruebas, ejecutar Ruff, generar cobertura y reproducir los checks de CI.

Comprobaciones rápidas con el entorno de pruebas preparado:

```bash
export DJANGO_SETTINGS_MODULE=config.settings_test
python manage.py check
python -m ruff check .
python -m coverage run manage.py test --noinput --verbosity 2
python -m coverage report
```

## Render y Supabase

`render.yaml` crea el servicio web y, antes de iniciar Gunicorn, ejecuta:

```bash
python manage.py migrate --noinput
python manage.py bootstrap_demo
```

Esto prepara las tablas, el usuario compartido de Sprint 1 y los tipos iniciales en
cada despliegue. Ambos comandos pueden repetirse de forma segura.

Configura `DATABASE_URL` en Render con la conexión PostgreSQL de Supabase y
`sslmode=require`. No guardes credenciales en el repositorio.

El health check `/health/` confirma que el proceso HTTP responde; no comprueba la
conexión con PostgreSQL. Para verificarla desde un entorno autorizado:

```bash
python manage.py shell -c 'from django.db import connection; connection.ensure_connection(); print("PostgreSQL conectado")'
```

El servicio desplegado debe configurar además el origen real del frontend en
`CORS_ALLOWED_ORIGINS`. Para autenticación con cookies también será necesario definir
`CSRF_TRUSTED_ORIGINS` y el flujo de sesión/CSRF.

## Contribuciones

Trabaja desde `main` actualizado en una rama corta y utiliza Conventional Commits.
Los pull requests ejecutan validación de commits, Ruff, Django checks y la suite
completa sobre PostgreSQL. La guía del equipo está en
[docs/validacion-backend.md](docs/validacion-backend.md).
