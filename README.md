# Eventger backend

Arranque de Django y Django REST Framework para Render. Expone `/` y `/health/`.
El health check comprueba que el servidor responde; no verifica Supabase.
Todavía no hay CRUD de eventos, login ni modelos del dominio.

## Desarrollo local

Requiere Python 3.12.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

Copia la clave generada en SECRET_KEY dentro de `.env`.

```bash
python manage.py check
python manage.py test config
python manage.py runserver
```

Abre http://127.0.0.1:8000/health/.

## Render

En Render selecciona **New > Blueprint**, conecta `Eventger/backend`, selecciona
`main` y aplica `render.yaml`. El archivo crea únicamente el servicio web Free;
no crea una base de datos Render. SECRET_KEY se genera automáticamente.
La URL real aparece en el panel cuando termina el despliegue.

También puedes crear un Web Service manual con:

- Runtime: Python 3.
- Branch: main. Root Directory: vacío.
- Build: `pip install -r requirements.txt`.
- Start: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --access-logfile - --error-logfile -`.
- Health check: `/health/`.
- Variables: SECRET_KEY (generada), DEBUG=false.
- El hostname de Render se agrega automáticamente a ALLOWED_HOSTS.

El servicio Free puede suspenderse por inactividad y tardar en responder al despertar.

## Supabase

Agrega DATABASE_URL en **Render > servicio > Environment**, usando la conexión
**Session pooler** de Supabase (puerto 5432), con `sslmode=require`.
Copia usuario y host exactamente desde Connect. Codifica los caracteres especiales
de la contraseña si construyes la URL manualmente. Nunca subas esa URL a GitHub.

Sin DATABASE_URL solo funciona el arranque HTTP. No hay una base SQLite alternativa.
Con DATABASE_URL se configura PostgreSQL; `/health/` sigue siendo una comprobación HTTP.
Para verificar la conexión desde un entorno seguro con las variables configuradas:

```bash
python manage.py shell -c 'from django.db import connection; connection.ensure_connection(); print("PostgreSQL conectado")'
```

Este arranque no ejecuta `migrate` automáticamente ni modifica las tablas existentes
creadas en Supabase. Antes de implementar el dominio, obtener el SQL verificable de usuarios, eventos
y subtareas y acordar su mapeo, integración con el usuario Django e historial de
migraciones. Los nombres provienen de la referencia visual y aún no están verificados. No ejecutar nuevas migraciones que
creen tablas duplicadas. Las vistas y triggers existentes también deben versionarse.

## Frontend y permisos

Cuando exista el frontend, agrega su origen exacto a CORS_ALLOWED_ORIGINS
(por ejemplo https://tu-frontend.vercel.app), sin barra final. Varios orígenes se
separan por comas. Para autenticación mediante cookies, configura también
CSRF_TRUSTED_ORIGINS y el flujo de sesión/CSRF antes de habilitarlo.

Los futuros endpoints DRF requieren autenticación por defecto. Cada consulta del
negocio debe filtrar por el organizador autenticado. No hay endpoints públicos de datos.

## Referencias

- https://render.com/docs/deploy-django
- https://render.com/docs/blueprint-spec
- https://supabase.com/docs/guides/database/connecting-to-postgres

## Validación automática y contribuciones

Consulta [la guía del equipo](docs/validacion-backend.md) para Conventional Commits,
PostgreSQL aislado, checks, cobertura, Sonar y pendientes de Supabase/Render.
La CI no requiere secretos de producción ni implementar HU futuras.
