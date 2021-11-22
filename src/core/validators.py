from django.apps import apps
from django.core.exceptions import ValidationError


def validate_showcase(value):
    if type(value) != list:
        raise ValidationError('showcase has to be a list', params={'value': value})
    for item in value:
        if type(item) != list:
            raise ValidationError(
                'showcase items have to be lists', params={'value': value}
            )
        if len(item) != 2:
            raise ValidationError(
                'showcase items have to contain 2 values', params={'value': value}
            )
        valid_sc_types = ['activity', 'album']
        if (sc_type := item[1]) not in valid_sc_types:
            raise ValidationError(
                f'showcase items have to be of these types: {valid_sc_types}',
                params={'value': value},
            )
        if type(sc_id := item[0]) != str:
            raise ValidationError(
                'showcase item ID has to be str', params={'value': value}
            )

        model_name = {'activity': 'Activity', 'album': 'Album'}
        model = apps.get_model('core', model_name[sc_type])
        try:
            model.objects.get(pk=sc_id)
        except model.DoesNotExist:
            raise ValidationError(
                f'showcase item ID {sc_id} does not exist', params={'value': value}
            )
