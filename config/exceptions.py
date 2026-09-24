from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler


ERROR_MESSAGES = {
    status.HTTP_400_BAD_REQUEST: "Los datos enviados no son válidos.",
    status.HTTP_401_UNAUTHORIZED: "No se proporcionaron credenciales válidas.",
    status.HTTP_403_FORBIDDEN: "No tienes permiso para realizar esta acción.",
    status.HTTP_404_NOT_FOUND: "El recurso solicitado no existe.",
    status.HTTP_405_METHOD_NOT_ALLOWED: (
        "El método HTTP no está permitido para este endpoint."
    ),
    status.HTTP_503_SERVICE_UNAVAILABLE: (
        "El servicio no está configurado para crear eventos."
    ),
}


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        return None

    response_data = {
        "success": False,
        "message": ERROR_MESSAGES.get(
            response.status_code,
            "No fue posible procesar la solicitud.",
        ),
    }

    if isinstance(exc, ValidationError):
        response_data["errors"] = response.data

    response.data = response_data
    return response
