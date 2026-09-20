# Evidencia local de la configuración de CI

Rama: `ci/backend-validation`. Base local y `origin/main`:
`dddd8a781be1ab9fde82e9991d5415ce2420f456`. `git ls-remote` confirmó ese mismo
SHA en main remoto durante la inspección. El árbol estaba limpio al iniciar.
No se realizaron commits, push, merge, despliegues ni cambios remotos.

## Archivos y propósito

- `.github/workflows/backend.yml`: cuatro checks, PostgreSQL, artifacts y Sonar opcional.
- `package.json`, `package-lock.json`, `commitlint.config.cjs`, `.githooks/commit-msg`:
  mensajes, títulos y hook local; Node solo para desarrollo.
- `requirements-ci.in`, `requirements-ci.txt`: herramientas separadas de producción,
  resolución fijada con hashes, incluidas dependencias transitivas.
- `config/settings_test.py`: conexión exclusivamente local sin heredar entorno real.
- `ci/runner.py`, `ci/test_database.py`: JUnit, rechazo de suite vacía y comprobación
  de la infraestructura PostgreSQL realmente utilizada por Django.
- `pyproject.toml`: Ruff y cobertura, sin umbral mínimo arbitrario.
- `sonar-project.properties`, `ci/sonar_properties.py`: fuentes/pruebas, importación
  de cobertura e identidad configurable sin guardar secretos.
- `.gitignore`: entornos, credenciales y resultados fuera del control de versiones.
- `README.md`, `docs/validacion-backend.md`, este informe y plantilla de PR:
  flujo del equipo, comandos, evidencias y decisiones pendientes.

## Verificaciones reales

| Comprobación | Resultado |
| --- | --- |
| Python 3.12.13 y dependencias con hashes | Instalación correcta en .venv |
| npm ci --ignore-scripts | Correcto; lockfile reproducible |
| actionlint 1.7.12 | Workflow válido |
| Ruff 0.16.8 | Sin errores |
| manage.py check con settings_test | Sin problemas |
| Cuatro pruebas HTTP originales | Conservadas y exitosas |
| Suite completa | 6 pruebas exitosas |
| PostgreSQL 17.9, Podman | Base creada desde cero, migraciones auth/contenttypes aplicadas, escritura sintética correcta, base de pruebas eliminada |
| JUnit y cobertura | reports/ y coverage.xml generados; 70 % (64/91 sentencias) |
| Commitlint | Español, scope opcional, Jira opcional y ambas formas breaking change aceptados |
| Mensajes inválidos | Rechazados con exit 1 |
| Rango de commits en repositorio temporal | Historial inválido anterior excluido; commit nuevo inválido rechazado |
| Hook local | Mensaje válido aceptado; inválido rechazado |
| Título de PR tipo merge | Rechazado; commits automáticos reconocidos conservan excepción |
| Entorno sintético de producción | DATABASE_URL, SECRET_KEY, RENDER y CORS no contaminan settings_test |
| Suite vacía | Rechazada con exit 1 |
| PostgreSQL inaccesible | Pruebas de infraestructura fallan con exit 1 |
| Aserción deliberadamente fallida en archivo temporal | Runner devuelve exit 1 |
| Configuración Sonar desactivada | Paso informa análisis no ejecutado |
| Sonar activado incompleto / Cloud sin organización | Paso falla con exit 1 |
| Sonar con parámetros sintéticos completos | Solo validación local de parámetros exitosa; no se ejecutó scanner |
| git diff --check | Sin errores de espacios |

Docker no tenía daemon disponible; se usó Podman para ejecutar la imagen fijada.
El contenedor temporal se detuvo y eliminó después de verificar. Los fallos deliberados
se probaron en archivos/repositorios temporales, sin dejar pruebas fallidas en la suite.
El hook se probó directamente; no se modificó core.hooksPath automáticamente.

## Límites y siguientes pasos

No se ejecutó GitHub Actions remotamente ni un scanner Sonar. El SQL de Supabase no
está disponible: faltan reconstrucción del dominio, restricciones, relaciones, mapeo
Django y compatibilidad con características específicas de Supabase. Tampoco se
verificó la conexión desplegada Render–Supabase o la espera de checks de Render.
Se requiere un SQL de solo esquema, sin datos ni credenciales, para completar esa fase.

La guía detalla variables `SONAR_ENABLED`, `SONAR_HOST_URL`, `SONAR_PROJECT_KEY`,
`SONAR_ORGANIZATION` y el secret `SONAR_TOKEN`; ningún secreto es necesario para CI
básica. El equipo debe revisar, publicar la rama y abrir PR para ejecutar Actions.
Después de confirmar instancia, edición, proyecto y conectividad, activar Sonar en
main con SONAR_ENABLED=true. No hacer Sonar obligatorio durante el diagnóstico.

Mensaje de commit sugerido:
`ci(backend): configurar validación, PostgreSQL aislado y Sonar opcional`
