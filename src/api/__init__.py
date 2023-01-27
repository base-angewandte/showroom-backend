import logging

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


class PermanentRedirect(APIException):
    status_code = status.HTTP_308_PERMANENT_REDIRECT
    default_detail = 'This resource has moved'
    default_code = 'permanent_redirect'

    def __init__(self, detail=None, to=None):
        if to is None:
            raise TypeError("PermanentRedirect is missing required argument 'to'")
        self.to = to
        if detail is None:
            detail = self.default_detail
        super().__init__(detail)


def showroom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    if isinstance(exc, PermanentRedirect):
        pk = context['kwargs']['pk']
        old_path = context['request']._request.path
        new_path = old_path.replace(pk, exc.to)
        response.data['to'] = new_path
        response.headers['Location'] = new_path

    return response
