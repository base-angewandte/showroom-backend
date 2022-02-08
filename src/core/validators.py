from django.apps import apps
from django.core.exceptions import ValidationError

from api.repositories.portfolio import activity_lists


def validate_common_list(value):
    if 'label' not in value or 'data' not in value or len(value.keys()) != 2:
        raise ValidationError(
            'CommonList has to have two keys: label, data', params={'value': value}
        )
    if type(value['label']) is not str:
        raise ValidationError(
            'CommonList label has to be string', params={'label': value['label']}
        )
    if type(value['data']) is not list:
        raise ValidationError(
            'CommonList data has to be list', params={'data': value['data']}
        )
    for item in value['data']:
        if type(item) is not dict:
            raise ValidationError(
                'CommonList data item has to be dict', params={'item': item}
            )
        # if the current item has a label in it, it has to be a nested CommonList
        # therefore we'll recursively validate it
        if 'label' in item:
            validate_common_list(item)
        # in all other cases it has to at least contain a value string
        else:
            if 'value' not in item:
                raise ValidationError(
                    'CommonList data item (if not another CommonList) has to have a value property',
                    params={'item': item},
                )
            if type(item['value']) is not str:
                raise ValidationError('value has to be str', params={'item': item})
            if 'source' in item and type(item['source']) is not str:
                raise ValidationError('source has to be str', params={'item': item})
            if 'url' in item and type(item['source']) is not str:
                raise ValidationError('url has to be str', params={'item': item})
            if 'attributes' in item:
                if type(item['attributes']) is not list:
                    raise ValidationError(
                        'attributes has to be list', params={'item': item}
                    )
                for attr in item['attributes']:
                    if type(attr) is not str:
                        raise ValidationError(
                            'attributes must only contain str values',
                            params={'item': item},
                        )
            if 'additional' in item:
                if type(item['additional']) is not list:
                    raise ValidationError(
                        'additional has to be list', params={'item': item}
                    )
                for additional in item['additional']:
                    additional_error = False
                    if type(additional) is not dict:
                        additional_error = True
                    else:
                        for k in ['label', 'value', 'url', 'source']:
                            if k in additional and type(additional[k]) is not str:
                                additional_error = True
                                break
                    if additional_error:
                        raise ValidationError(
                            'additional item has to be dict containing string properties',
                            params={'item': additional},
                        )


def validate_entity_list(value):
    if type(value) != dict:
        raise ValidationError('list has to be a dict', params={'value': value})
    for key in value:
        if key not in activity_lists.list_collections:
            raise ValidationError(
                'key is not a valid activity list collection',
                params={'key': key},
            )
        if type(value[key]) is not dict:
            raise ValidationError(
                'list properties have to be of type dict',
                params={'key': key, 'value': value[key]},
            )
        for lang in value[key]:
            if type(lang) is not str or len(lang) != 2:
                raise ValidationError(
                    'LocalisedCommonList keys have to be 2-letter language codes',
                    params={'list': key, 'key': lang},
                )
            validate_common_list(value[key][lang])


def validate_list_ordering(value):
    if type(value) != list:
        raise ValidationError('list_ordering has to be a list', params={'value': value})
    for item in value:
        if type(item) != dict:
            raise ValidationError(
                'list_ordering items have to be of type dict', params={'item': item}
            )
        if 'id' not in item or 'hidden' not in item or len(item.keys()) != 2:
            raise ValidationError(
                'item has to have two keys: id, hidden', params={'item': item}
            )
        if type(item['id']) is not str:
            raise ValidationError('item["id"] has to be str', params={'item': item})
        if type(item['hidden']) is not bool:
            raise ValidationError(
                'item["hidden"] has to be bool', params={'item': item}
            )
        if item['id'] not in activity_lists.list_collections:
            raise ValidationError(
                'item["id"] is not a valid activity list collection',
                params={'item': item},
            )


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
