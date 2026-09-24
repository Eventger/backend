from rest_framework.exceptions import APIException


class DemoUserNotConfigured(APIException):
    status_code = 503
    default_detail = "El usuario demo no está configurado."
    default_code = "demo_user_not_configured"
