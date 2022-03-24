import requests

from django.conf import settings

from core.models import ShowroomObject, SourceRepository


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
        settings.CAS_API_BASE + f'user-data-agent/{username}/', headers=auth_headers
    )

    if r.status_code == 403:
        raise UserPrefAuthenticationError(f'Authentication failed. 403: {r.text}')
    elif r.status_code == 404:
        raise UserPrefNotFoundError(f'No user data found for {username}. 404: {r.text}')
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
        try:
            default_user_repo = SourceRepository.objects.get(
                id=settings.DEFAULT_USER_REPO
            )
        except SourceRepository.DoesNotExist:
            raise UserPrefError('Configured SourceRepository does not exist!')

        try:
            entity = ShowroomObject.objects.get(
                source_repo_entry_id=username,
                source_repo_id=settings.DEFAULT_USER_REPO,
            )
            entity.source_repo_data = result
            entity.save()
        except ShowroomObject.DoesNotExist:
            entity = ShowroomObject.objects.create(
                source_repo_entry_id=username,
                source_repo=default_user_repo,
                source_repo_data=result,
            )
        entity.update_from_repo_data()
        entity.update_activities()

    return result
