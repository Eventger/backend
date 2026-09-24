from drf_spectacular.utils import OpenApiExample


EVENT_CREATE_EXAMPLES = [
    OpenApiExample(
        "Solicitud válida",
        value={
            "name": "Boda de Ana y Luis",
            "type": 1,
            "date": "2026-11-15T18:00:00-05:00",
            "location": "Cali",
            "contact": "Ana Rodríguez - 300 123 4567",
        },
        request_only=True,
    ),
    OpenApiExample(
        "Evento creado",
        value={
            "success": True,
            "message": "Evento creado correctamente.",
            "data": {
                "id": 3,
                "user": 4,
                "name": "Boda de Ana y Luis",
                "type": 1,
                "date": "2026-11-15T18:00:00-05:00",
                "location": "Cali",
                "contact": "Ana Rodríguez - 300 123 4567",
                "created_at": "2026-09-23T19:30:00-05:00",
                "updated_at": "2026-09-23T19:30:00-05:00",
            },
        },
        response_only=True,
        status_codes=["201"],
    ),
    OpenApiExample(
        "Campos requeridos",
        value={
            "success": False,
            "message": "Los datos enviados no son válidos.",
            "errors": {
                "name": ["Este campo es requerido."],
                "type": ["Este campo es requerido."],
                "date": ["Este campo es requerido."],
                "location": ["Este campo es requerido."],
                "contact": ["Este campo es requerido."],
            },
        },
        response_only=True,
        status_codes=["400"],
    ),
    OpenApiExample(
        "Usuario demo no configurado",
        value={
            "success": False,
            "message": "El servicio no está configurado para crear eventos.",
        },
        response_only=True,
        status_codes=["503"],
    ),
]


SUBTASK_CREATE_EXAMPLES = [
    OpenApiExample(
        "Solicitud válida",
        value={
            "name": "Confirmar servicio de catering",
            "target_date": "2026-11-10T09:00:00-05:00",
            "estimated_hours": "2.50",
            "details": "Confirmar menú y cantidad de invitados.",
        },
        request_only=True,
    ),
    OpenApiExample(
        "Subtarea creada",
        value={
            "success": True,
            "message": "Subtarea creada correctamente.",
            "data": {
                "id": 8,
                "event": 3,
                "state": "pending",
                "name": "Confirmar servicio de catering",
                "target_date": "2026-11-10T09:00:00-05:00",
                "estimated_hours": "2.50",
                "details": "Confirmar menú y cantidad de invitados.",
                "created_at": "2026-09-23T19:35:00-05:00",
                "updated_at": "2026-09-23T19:35:00-05:00",
            },
        },
        response_only=True,
        status_codes=["201"],
    ),
    OpenApiExample(
        "Horas estimadas inválidas",
        value={
            "success": False,
            "message": "Los datos enviados no son válidos.",
            "errors": {
                "estimated_hours": [
                    "Las horas estimadas deben ser mayores que 0."
                ],
            },
        },
        response_only=True,
        status_codes=["400"],
    ),
    OpenApiExample(
        "Evento inexistente",
        value={
            "success": False,
            "message": "El evento no existe.",
        },
        response_only=True,
        status_codes=["404"],
    ),
]


SUBTASK_STATE_UPDATE_EXAMPLES = [
    OpenApiExample(
        "Completar subtarea",
        value={"state": "completed"},
        request_only=True,
    ),
    OpenApiExample(
        "Estado actualizado",
        value={
            "success": True,
            "message": "Subtarea actualizada correctamente.",
            "data": {
                "id": 8,
                "event": 3,
                "state": "completed",
                "name": "Confirmar servicio de catering",
                "target_date": "2026-11-10T09:00:00-05:00",
                "estimated_hours": "2.50",
                "details": "Confirmar menú y cantidad de invitados.",
                "created_at": "2026-09-23T19:35:00-05:00",
                "updated_at": "2026-09-23T19:45:00-05:00",
            },
        },
        response_only=True,
        status_codes=["200"],
    ),
    OpenApiExample(
        "Estado inválido",
        value={
            "success": False,
            "message": "Los datos enviados no son válidos.",
            "errors": {
                "state": ["\"invalid\" no es una elección válida."],
            },
        },
        response_only=True,
        status_codes=["400"],
    ),
]
