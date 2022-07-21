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
        if exc.to:
            new_path = old_path.replace(pk, exc.to)
            response.data['to'] = new_path
            response.headers['Location'] = new_path
        else:
            # TODO: in case to was not set when the exception was raised, should we
            #       rather convert this to a 404, or should we even raise another
            #       exception and go for a 500?
            response.data['to'] = 'location not disclosed'
            logger.warning(
                f'PermanentRedirect: no to parameter was provided for {old_path}'
            )

    return response
