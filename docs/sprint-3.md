# Sprint 3: capacidad y reprogramación

El límite se guarda en `users_user.daily_limit_hours`, con 6 h por defecto y un
CHECK de PostgreSQL entre 1 y 16. Cada organizador conserva un valor independiente.
La migración local `0002_alter_user_options_user_daily_limit_configured_and_more`
depende de `0002_user_daily_limit_hours`, ya integrada en main: modifica el campo
existente y añade `daily_limit_configured` y el CHECK. `0003_alter_user_options`
se conserva como paso sin operaciones. No eliminan usuarios, eventos ni tareas.
Se verifica la cadena en PostgreSQL aislado; no se aplican cambios a la BD de
trabajo ni a producción. Si un entorno aplicó las versiones locales anteriores
antes de integrar main, hay que reconciliar su historial de migraciones y esquema
antes de desplegar; no ejecutar `--fake` sin verificar ambos.

## Contrato

Todas las rutas requieren la sesión Clerk existente (`Authorization: Bearer …`).
Nunca se recibe un ID de organizador para elegir el propietario.

| Método | Ruta | Resultado |
| --- | --- | --- |
| GET | `/api/auth/preferences/` | `{success: true, data: {daily_limit_hours: "6.00", daily_limit_configured: false}}` |
| PUT | `/api/auth/preferences/` | Guarda `{daily_limit_hours: "4.50"}`. Rango 1–16, hasta dos decimales; HTTP 400 si es inválido. |
| POST | `/subtasks/{id}/reschedule-preview/` | Evalúa `{target_date: "2026-10-12", estimated_hours: "2.00"}` sin escribir. Las horas son opcionales; usa las actuales si faltan. |
| PATCH/PUT | `/subtasks/{id}/` | Conserva el contrato de edición y añade `planning` al éxito. HTTP 409 si un cambio de fecha/horas o reactivación causa sobrecarga. |

PUT de preferencias admite `only_if_unconfigured: true` para importar una
preferencia anterior de Clerk sin reemplazar una elección guardada mientras se
procesa la importación. La condición se comprueba dentro de la misma transacción.

La vista previa devuelve `date`, `event_date`, `existing_hours`, `added_hours`,
`planned_hours`, `daily_limit_hours`, `overload_hours`, `has_conflict`, las tareas
existentes de ese día y una `suggestion` con fecha y carga resultante, o `null`.
Un 409 usa `{success: false, message: "…", data: <vista previa actualizada>}` y
no persiste ninguno de los cambios de la tarea, incluidos nombre y nota.

## Decisiones e iteración

- Se conserva el CRUD de Sprint 1 y la autenticación de Sprint 2. Las ediciones
  de nombre/nota y marcar completada siguen funcionando en un día sobrecargado.
- La carga suma tareas pendientes/en progreso de todos los eventos del mismo
  organizador, excluye completadas y excluye la tarea candidata antes de añadir
  sus horas. El calendario es `America/Bogota`, también para timestamps UTC.
- La vista previa permite prevenir errores, pero el guardado vuelve a calcular
  dentro de una transacción con bloqueo del organizador. Dos reprogramaciones o
  un cambio de límite no pueden basarse simultáneamente en un límite obsoleto.
  La creación de tareas comparte ese bloqueo y conserva el comportamiento previo;
  este sprint no impone un bloqueo nuevo a la creación de planes iniciales.
- Se sugiere el primer día viable del intervalo de 30 días desde la fecha inicial
  de búsqueda, sin pasar la fecha del evento. Si no existe, se indica y se permite
  seleccionar otra fecha válida manualmente o reducir la estimación.
- Se probaron el caso 5+2>6, el caso 4+2=6, límites 1/16, aislamiento entre
  organizadores, resolución por fecha/horas, vista previa obsoleta y dos escrituras
  concurrentes. `apps/subtasks/tests/test_planning.py` contiene la regresión.

Validación local del 3 de octubre de 2026: suite completa de 128 pruebas aprobada
sobre PostgreSQL aislado (13 específicas de planificación, incluida concurrencia).
Las 13 se repitieron después del ajuste final del intervalo de sugerencias;
`ruff check`, `manage.py check` y `makemigrations --check --dry-run` aprobaron.

## Eliminación de cuenta

`DELETE /api/auth/me/` exige el encabezado `X-Account-Deletion-Confirmation: ELIMINAR`
y devuelve 204 sin cuerpo al completar el borrado. Usa exclusivamente el organizador autenticado;
no admite seleccionar otro usuario ni borrar los tipos globales de eventos.
El encabezado está habilitado en CORS para los orígenes permitidos existentes;
no se habilitan nuevos dominios ni orígenes globales.
Comprueba que el `sub` verificado coincide con `clerk_id` y que `fva` cumple la
política [strict de Clerk](https://clerk.com/docs/guides/secure/reverification):
menos de 10 minutos desde el segundo factor, o desde el primero cuando no hay
segundo. Un 403 con `clerk_error` solicita reverificación en el frontend. No hay
escrituras ni llamadas al proveedor antes de validar confirmación e identidad.

El servicio bloquea el organizador, comprueba en Clerk que permite la eliminación
propia, borra sus eventos (con tareas en cascada) y el usuario dentro de una
transacción. La eliminación explícita de eventos evita que `SET_NULL` deje datos
huérfanos. Finalmente elimina la identidad usando la clave Clerk del servidor,
con timeout de 8 s y sin reintentos automáticos. Un rechazo o fallo de transporte
revierte los cambios locales y devuelve 503; no expone respuestas del proveedor.
Un 404 de Clerk se considera una identidad ya eliminada y permite completar la
limpieza local. El frontend sólo cierra sesión después del 204.

Clerk y PostgreSQL no comparten una transacción: si Clerk acepta y se pierde su
respuesta, o falla el commit de PostgreSQL después, la identidad puede quedar
eliminada y los datos locales conservados. El servicio permite completar un
reintento autenticado cuando Clerk devuelve 404. Si la sesión ya no permite ese
reintento, se requiere reconciliación operativa del organizador en el backend;
no se anuncia éxito en el frontend ni se borra información de otra cuenta.
Un token aún no vencido no puede recrear el usuario después del borrado local:
al provisionar un usuario nuevo, la autenticación verifica que existe en Clerk.
No se implementa un webhook para borrados iniciados fuera de Eventger.

Las pruebas de API sustituyen Clerk y comprueban propiedad, reverificación,
confirmación, rollback, reintentos y tokens de una identidad eliminada. No se
ejecutan eliminaciones sobre cuentas reales.

## Local

El entorno existente usa Podman y `eventger-postgres-local`. Arranque:

```bash
podman start eventger-postgres-local
DEBUG=true .venv/bin/python manage.py runserver 127.0.0.1:8000
```

`DEBUG=true` evita heredar el modo de producción del shell en el arranque local.
No cambia `.env`, las claves de Clerk ni los ajustes del despliegue.

Las pruebas utilizan PostgreSQL aislado en 55432 mediante
`DJANGO_SETTINGS_MODULE=config.settings_test`. No ejecutarlas sobre la BD local
de trabajo ni sobre Supabase. Swagger y el esquema siguen en `/api/docs/` y
`/api/schema/`; la documentación anterior de Clerk genera avisos de esquema
preexistentes, que no equivalen a errores de autenticación HTTP.

## Corrección de plazos (7 de octubre de 2026)

La vista previa rechaza fechas anteriores a hoy en Bogotá. PATCH y PUT rechazan
mover una tarea al pasado con HTTP 400 y `errors.target_date`, sin guardar el resto
de los cambios. Se permite conservar una fecha histórica al editar una tarea ya
vencida; esta regla no impide actualizar notas, duración o estado sin moverla.

El guardado de reprogramación también rechaza una fecha posterior al evento con
HTTP 400 y `errors.target_date`, aun si una vista previa anterior era válida.
La edición de la fecha del evento rechaza dejar tareas después del nuevo día y
responde con `errors.date`, identificando hasta cinco tareas para reprogramar.
Se utiliza el calendario de Bogotá: una tarea y un evento pueden compartir día
sin exigir que coincidan sus timestamps. El cambio del evento y la reprogramación
comparten el bloqueo del organizador; una escritura concurrente no puede validar
contra el plazo anterior. Se conserva la posibilidad de completar o anotar tareas
con fechas inconsistentes heredadas cuando no se modifica su fecha.

Las regresiones comprueban PATCH/PUT, ausencia de escrituras parciales, misma fecha
en Bogotá, vista previa obsoleta y concurrencia entre evento y tarea. La suite
completa del backend pasó con 199 pruebas en PostgreSQL aislado.
