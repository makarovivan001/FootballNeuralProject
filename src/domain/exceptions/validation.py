from rest_framework.exceptions import APIException
from rest_framework.status import HTTP_400_BAD_REQUEST

class ValidationAPIError(APIException):
    status_code = HTTP_400_BAD_REQUEST
    default_detail = "Неверные данные"
