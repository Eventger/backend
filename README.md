# Eventger backend

API REST construida con Django y Django REST Framework para gestionar eventos y
subtareas logísticas, con autenticación Clerk y datos por organizador.
El límite diario y los contratos de reprogramación de Sprint 3 están documentados
en [docs/sprint-3.md](docs/sprint-3.md).

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
python manage.py bootstrap_initial_data
```

`bootstrap_initial_data` crea de forma idempotente el catálogo inicial de tipos de
evento. Puede ejecutarse varias veces sin duplicar registros.

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
| GET, POST | `/events/` | Listar eventos paginados (6 por página) y crear eventos del organizador autenticado |
| GET, PUT, PATCH, DELETE | `/events/{id}/` | Consultar, actualizar o eliminar un evento |
| GET | `/event-types/` | Listar tipos de evento |
| GET, POST | `/events/{event_id}/subtasks/` | Listar o crear subtareas dentro de un evento |
| GET | `/subtasks/` | Listar subtareas del organizador autenticado |
| GET | `/hoy/` | Listar subtareas agrupadas por fecha; admite `status` y `event` como filtros |
| GET, PUT, PATCH, DELETE | `/subtasks/{id}/` | Consultar, actualizar o eliminar una subtarea |
| POST | `/subtasks/{id}/reschedule-preview/` | Consultar carga y alternativas sin guardar |
| GET, PUT | `/api/auth/preferences/` | Consultar o guardar el límite diario de 1–16 horas |
| DELETE | `/api/auth/me/` | Eliminar la cuenta Clerk y los datos propios de Eventger, con confirmación y reverificación reciente |

`POST /subtasks/` no está habilitado. Toda subtarea debe crearse mediante la ruta
del evento al que pertenece.

`GET /hoy/` acepta `status` (`pending`, `in_progress` o `completed`) y `event`
(ID del evento) como parámetros de consulta. Los filtros pueden combinarse.
Cada tarea incluye `event_name`, obtenido junto con su evento para evitar una
consulta adicional por tarea y la descarga completa de `/events/` desde Hoy.

`GET /events/?page=2` devuelve hasta 6 eventos en `data`, con el formato habitual
`success`, y añade `pagination`: `page`, `page_size` (siempre 6), `total` y
`total_pages`. El conteo y los resultados pertenecen únicamente al usuario
autenticado. El orden es fecha descendente y, en empates, ID descendente. `page`
es un entero positivo y vale 1 si se omite; los valores inválidos devuelven 400.
Una página superior al total se ajusta a la última disponible, también tras una
eliminación. Una cuenta vacía devuelve `data: []`, página 1 y total 0.

El parámetro opcional `type` es el ID positivo de un tipo de `/event-types/`:
`GET /events/?page=2&type=1`. Se aplica antes del conteo y la paginación, siempre
dentro de los eventos del usuario autenticado. Omitirlo o dejarlo vacío devuelve
todos los tipos; un valor no numérico o no positivo devuelve 400. Un tipo sin
coincidencias devuelve una lista vacía y total 0, también si ya no existe.

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
python manage.py bootstrap_initial_data
```

Esto prepara las tablas y los tipos iniciales en cada despliegue. Ambos comandos
pueden repetirse de forma segura.

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
