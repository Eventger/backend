# Validación del Backend

## Flujo del equipo

Trabajar desde `main` actualizado en ramas cortas (`ci/...`, `feat/...`, `fix/...`).
Integrar aportes funcionales pequeños con commits progresivos por subtarea. No usar
`develop`. No es necesario completar toda una HU para integrar una parte que conserva
el funcionamiento existente. Aprobar un aporte no significa cerrar una HU.

Propuesta para GitHub, **no aplicada remotamente**: PR obligatorio hacia `main`, una
aprobación de otro integrante, conversaciones resueltas, impedir push directo y force
push, squash merge con título Conventional Commit. Checks obligatorios propuestos:
`Conventional Commits`, `Comprobaciones de Python y Django`, `Pruebas Backend`.
Dejar `Análisis Sonar` opcional durante el diagnóstico inicial.

## Preparación local

Python **3.12.13**, Node **24.18.0** (solo desarrollo) y Docker o Podman.
Las dependencias de producción y los comandos de Render permanecen intactos.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --require-hashes -r requirements-ci.txt
npm ci --ignore-scripts
npm run hooks:install
```

`hooks:install` cambia únicamente `core.hooksPath` en este checkout; revisar un hook
anterior antes de instalar. No se instala automáticamente. Actions valida aunque
el integrante no lo haya instalado. El hook requiere ejecutar el commit desde este
repositorio y tener Node y las dependencias instaladas.

```text
feat(subtasks): validar horas estimadas positivas

Refs: M1P-13
```

Scope y Jira son opcionales; se permite español y mayúsculas en la descripción.
Tipos: feat, fix, docs, test, refactor, perf, style, build, ci, chore, revert.
Se aceptan `feat!: cambiar contrato` y el pie `BREAKING CHANGE: explicación`.
Los mensajes automáticos de merge/revert reconocidos por commitlint conservan sus
excepciones predeterminadas para commits. El título del PR no tiene esas excepciones.
Ante un error, el log muestra el mensaje y la regla: corregir con `git commit --amend`
o rebase local de los commits propios; coordinar cualquier actualización de una rama
compartida. No reescribir `main`.

En PR se valida `base.sha..head.sha`, **no** el SHA del merge sintético. Se recupera
el historial completo para resolver ese rango; no se valida retroactivamente el
historial de main. También se valida el título al editar el PR. Código y pruebas sí
validan el checkout de integración que proporciona GitHub. Fuera de PR, el check de
commits informa que no aplica; la protección propuesta exige pasar por PR.

## PostgreSQL aislado y comandos

PostgreSQL **17.9** es una elección provisional: falta confirmar la versión real de
Supabase. El servicio es desechable; sus credenciales son públicas y exclusivas de
pruebas, nunca se reutilizan en producción. Arranque local (usar `podman` en lugar de
`docker` si corresponde):

```bash
docker run --detach --rm --name eventger-ci \
  -e POSTGRES_DB=eventger_ci -e POSTGRES_USER=eventger_ci \
  -e POSTGRES_PASSWORD=eventger_ci_only \
  -p 127.0.0.1:55432:5432 postgres:17.9-bookworm
docker exec eventger-ci pg_isready -U eventger_ci -d eventger_ci
export DJANGO_SETTINGS_MODULE=config.settings_test
python manage.py check
python -m ruff check .
python -m coverage run manage.py test --noinput --verbosity 2
python -m coverage xml
python -m coverage report
docker stop eventger-ci
```

Esperar que `pg_isready` tenga éxito antes de ejecutar la suite. Si falla una prueba,
ejecutar igualmente los comandos de cobertura para conservar la evidencia; el fallo
original sigue siendo un fallo. Actions hace esto automáticamente sin ocultarlo.

`config.settings_test` carga los settings comunes bajo un entorno temporal limpio
con `.env` desactivado; después sustituye la conexión por PostgreSQL en `127.0.0.1`.
No hereda DATABASE_URL, SECRET_KEY, RENDER, CORS ni SSL del entorno real. Solo acepta
`TEST_POSTGRES_PORT` para variar el puerto local (55432 por defecto). No hay fallback
a SQLite. Esto no altera los settings ni los permisos de producción.

Orden actual: servicio vacío → Django crea **test_eventger_ci** → migraciones de
`auth` y `contenttypes` → suite → eliminación de la base de pruebas. Se necesitan
permisos CREATEDB en este servicio dedicado. No usar `--keepdb` para demostrar la
reconstrucción. Las dos pruebas de infraestructura verifican la base efectiva y una
escritura sintética mediante las tablas Django. No representan pruebas del dominio.
Las cuatro pruebas HTTP originales se conservan. El runner rechaza suites vacías y
sigue usando unittest/Django, añadiendo JUnit con unittest-xml-reporting.

Evidencias locales: `reports/TEST-*.xml`, `coverage.xml` y salida del runner. En Actions:
artifact `backend-evidence-<SHA>` de esa ejecución, retenido 14 días, incluso si falla
la suite y hay archivos disponibles. No hay porcentaje mínimo global arbitrario.
Ruff selecciona E4/E7/E9/F: errores y problemas estáticos, sin reforma de estilo.
Actualizar `requirements-ci.txt` al cambiar producción o herramientas:
`uv pip compile requirements-ci.in --generate-hashes -o requirements-ci.txt`.
Actualizar Node con npm y versionar siempre package-lock.json.

## Qué falta verificar de Supabase

No hay SQL, modelos de dominio ni migraciones propias en este repositorio. Se
requiere **un archivo SQL de solo esquema, sin datos ni credenciales**, de las tablas
`public.usuarios`, `public.eventos`, `public.subtareas` y sus dependencias. No se ha
consultado Supabase ni se ha inventado DDL. La referencia visual no prueba longitudes,
precisión, nulls, defaults, UNIQUE, CHECK, índices, cascadas, RLS, funciones o triggers.

Cuando llegue el SQL: revisar si solo es referencial, ordenar su creación, identificar
extensiones/roles/esquemas/funciones y versionar una reconstrucción aislada. Cargar el
DDL **en test_eventger_ci después de que el runner la cree**, mediante preparación
del runner, no solo en eventger_ci. Asignar un único dueño a cada tabla: migraciones
Django para auth/contenttypes y SQL verificado para dominio externo/unmanaged. No
crear migraciones productivas que dupliquen tablas. Validar desde cero columnas,
restricciones, UUID, FK, inserciones sintéticas y rechazo de referencias inexistentes.
Si surgen modelos unmanaged, incluir sus tablas por ese mecanismo y probar su mapeo.

Mapa pendiente, sin renombrar API ni base automáticamente:

| Descripción HU | Columna de la referencia |
| --- | --- |
| event_id | evento_id |
| estimated_hours | horas_estimadas |
| target_date | fecha_objetivo |
| Nombre de subtarea | titulo |

Revisar db_table/db_column, UUID y relaciones al implementar modelos. `public.usuarios`
no equivale automáticamente a `auth_user`. HU1 menciona cliente, pero la referencia
no muestra esa columna. ON DELETE debe comprobarse en SQL; varchar no determina los
estados válidos. Falta decidir/verificar si `horas_estimadas > 0` se exige en base,
aplicación o ambas. No simular restricciones inexistentes en la base de pruebas.

Tres evidencias distintas: (1) PostgreSQL aislado con Django, (2) compatibilidad con
RLS/extensiones y otras características Supabase, (3) conexión Render–Supabase. La
primera no demuestra las otras. La configuración actual interpreta DATABASE_URL como
PostgreSQL y exige SSL cuando DEBUG=false, pero la conexión desplegada y el mapeo del
dominio **no están verificados**. No ejecutar pruebas de escritura allí.

## Actions y Sonar

Para activar CI: revisar los cambios, crear el commit, publicar la rama y abrir PR a
main cuando el equipo lo autorice. Si Actions está deshabilitado, habilitarlo desde
Settings y permitir las Actions usadas. Este trabajo no hace push, merge ni cambios
remotos. La ejecución manual está disponible cuando el workflow exista en main.
No se necesitan secretos para los tres checks básicos.

Solo hay triggers push a main, PR a main y manual. Editar el título repite los checks;
no hay push adicional a ramas cortas. Se cancelan ejecuciones anteriores del mismo PR;
main y otros PR conservan sus ejecuciones. Se usa pull_request, permisos contents:read,
timeouts, SHA de Actions verificados y cachés por lockfile. No hay filtros por paths,
Jira o texto de commits, ni pull_request_target.

Sonar está preparado como proyecto Backend independiente. Por defecto indica
**“análisis no ejecutado”** en main/manual. No se analiza ningún PR ni otra rama.
Community Build documenta análisis de main; verificar edición y capacidades reales
antes de añadir PR/ramas (Server requiere una edición compatible; Cloud depende del
plan). No se ha contratado ni aprovisionado nada.

Configurar en GitHub Settings → Secrets and variables → Actions:

| Tipo | Nombre | Valor a configurar |
| --- | --- | --- |
| Variable | SONAR_ENABLED | `true` solo cuando todo esté listo; ausente/false desactiva |
| Variable | SONAR_HOST_URL | URL real HTTPS alcanzable por el runner |
| Variable | SONAR_PROJECT_KEY | Clave del proyecto Backend existente |
| Variable | SONAR_ORGANIZATION | Organización real si se usa Cloud; omitir para Server |
| Secret | SONAR_TOKEN | Token de análisis del proyecto; nunca en chat o repositorio |

Faltan instancia/edición, proyecto y credenciales. Un servidor en el computador del
equipo no se alcanza mediante localhost desde GitHub: requiere conectividad segura
acordada o runner dedicado. No ejecutar PR no confiables en ese runner. Verificar que
la rama principal del proyecto Sonar corresponda a main antes de activar.

Con SONAR_ENABLED=true y datos incompletos, el job falla con el nombre de la variable
faltante sin mostrar su valor. Usa cobertura del job tests del **mismo run y SHA**;
no busca “la última ejecución”. Sonar solo corre tras pruebas exitosas. Errores técnicos
fallan; `sonar.qualitygate.wait=false` evita imponer inicialmente un Quality Gate.
Scanner exitoso significa envío, no procesamiento terminado ni Quality Gate aprobado;
consultar la tarea y el resultado en Sonar. Para exigir calidad de código nuevo después,
acordar y fijar referencia/versión y condiciones del gate; no mover la referencia para
ocultar deuda. Incorporar la espera del gate solo cuando esté acordado.

## Render

render.yaml y requirements.txt se conservan; no se añade despliegue desde Actions ni
migraciones al arranque. Un cambio integrado a main puede disparar despliegue. CI y
Render tienen resultados distintos: **un workflow fallido no garantiza que Render
espere**. Revisar en el panel el servicio, rama, revisión desplegada y Auto-Deploy;
Render ofrece “After CI Checks Pass”, pero aquí no se ha comprobado ni cambiado esa
opción. No asumir que render.yaml refleja toda la configuración real del panel.

Smoke test de solo lectura propuesto, no ejecutado: tras identificar el SHA desplegado,
hacer GET a `/` y `/health/`, comprobar HTTP 200 y JSON esperado y registrar SHA,
fecha y respuesta. `/health/` no comprueba Supabase. Verificar la conexión SQL por
separado desde un entorno autorizado, sin registrar URL ni credenciales.

## Pruebas progresivas por HU

Toda la suite rápida se ejecuta en cada PR; conservar como regresión las pruebas que
se incorporen junto con la implementación. No añadir requisitos de funcionalidades
futuras a esta CI ni marcar historias como terminadas automáticamente.

| HU / Jira | Pruebas a incorporar con su implementación |
| --- | --- |
| US-01 / M1P-5 | Crear evento: datos válidos/inválidos y persistencia |
| US-02 / M1P-10 | Asociación de subtarea, horas numéricas positivas, persistencia y errores |
| US-03 / M1P-15 | Editar/eliminar: validación, persistencia e integridad acordada |
| US-04 / M1P-20 | Si la lógica es Backend: excluir terminadas, agrupar por fecha, ordenar y desempatar por menor esfuerzo |

Backend implementa y prueba su código. QA comprueba aceptación y consolida evidencias.
El flujo completo requiere identificar versiones de Frontend y Backend. Actualmente
DRF exige IsAuthenticated por defecto y están instalados auth/contenttypes de Django;
no hay login, modelo de usuario de dominio ni endpoints CRUD. Las tareas de autenticación
de Sprint 2+ requieren acordar su integración; no abrir endpoints ni cambiar permisos,
AUTH_USER_MODEL o almacenamiento de contraseñas para adelantar las HU.

## Fuentes oficiales consultadas

- [Commitlint CI y rango de PR](https://commitlint.js.org/guides/ci-setup)
- [Reglas commitlint](https://commitlint.js.org/reference/rules.html)
- [Django: runner y base de pruebas](https://docs.djangoproject.com/en/5.2/topics/testing/overview/)
- [Configuración Ruff](https://docs.astral.sh/ruff/configuration/)
- [SonarQube Community Build: alcance](https://docs.sonarsource.com/sonarqube-community-build/analyzing-source-code/analysis-overview)
- [Action oficial de Sonar](https://github.com/SonarSource/sonarqube-scan-action)
- [Render: despliegues y espera de CI](https://render.com/docs/deploys)

Versiones fijadas verificadas en releases de los repositorios oficiales de Actions,
registro npm y PyPI. Revisarlas deliberadamente al actualizar, junto con lockfiles.
