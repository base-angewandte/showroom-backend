from drf_spectacular.utils import OpenApiExample, OpenApiResponse, inline_serializer
from rest_framework import serializers

error_schema = inline_serializer(
    name='Error',
    fields={
        'detail': serializers.CharField(help_text='A message describing the error'),
    },
)


def error(
    description: str = 'A generic error response',
    detail: str = 'A message describing the error',
    status_code: int = None,
):
    status_codes = (
        [str(status_code)]
        if status_code
        else ['400', '401', '403', '404', '405', '500']
    )
    return OpenApiResponse(
        description=description,
        response=error_schema,
        examples=[
            OpenApiExample(
                name='Error',
                value={'detail': detail},
                # all response codes that will potentially use this example have to be listed here:
                status_codes=status_codes,
            ),
        ],
    )


class Responses:
    Error400 = error(
        status_code=400,
        description='Bad Request',
        detail='Something with your request is wrong. This message should provide more details.',
    )
    Error403 = error(
        status_code=403,
        description='Forbidden',
        detail='Authentication credentials were not provided.',
    )  # this is the DRF default reply for 404
    Error404 = error(
        status_code=404, description='Not Found', detail='Not found.'
    )  # this is the DRF default reply for 404
