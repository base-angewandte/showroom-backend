import logging

import requests

from django.conf import settings

from core.models import ShowroomObject, SourceRepository

logger = logging.getLogger(__name__)


class UserPrefError(Exception):
    pass


class UserPrefAuthenticationError(UserPrefError):
    pass


class UserPrefNotFoundError(UserPrefError):
    pass


auth_headers = {
    'X-Api-Key': settings.USER_PREFERENCES_API_KEY,
}


def pull_user_data(username, update_entry=True):
    r = requests.get(
        settings.CAS_API_BASE + f'users/{username}/',
        headers=auth_headers,
    )

    if r.status_code == 403:
        raise UserPrefAuthenticationError(f'Authentication failed. 403: {r.text}')
    elif r.status_code == 404:
        # if users are not found, we just want to log a warning, but not raise an error
        # users who exist in the auth backend but haven't logged in through CAS will
        # also not be found
        logger.warning(f'No user data found for {username}. 404: {r.text}')
        return {}
    elif r.status_code == 400:
        raise UserPrefError(
            f'User preferences for user {username} could not be pulled: 400: {r.text}'
        )
    elif r.status_code == 200:
        result = r.json()
    else:
        raise UserPrefError(
            f'Undefined error when fetching {username}. {r.status_code}: {r.text}'
        )

    if update_entry:
        if not SourceRepository.objects.filter(id=settings.DEFAULT_USER_REPO).exists():
            raise UserPrefError('Configured SourceRepository does not exist!') from None

        entity, created = ShowroomObject.objects.get_or_create(
            source_repo_object_id=username,
            source_repo_id=settings.DEFAULT_USER_REPO,
            defaults={'type': ShowroomObject.PERSON},
        )
        entity.source_repo_data = result
        entity.save()
        entity.entitydetail.update_from_repo_data()
        entity.entitydetail.update_activities()

    return result
