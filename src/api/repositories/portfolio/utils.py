from api.repositories.portfolio import get_preflabel

role_fields = [
    'architecture',
    'authors',
    'artists',
    'winners',
    'granted_by',
    'jury',
    'music',
    'conductors',
    'composition',
    'organisers',
    'lecturers',
    'design',
    'commissions',
    'editors',
    'publishers',
    'curators',
    'fellow_scholar',
    'funding',
    'organisations',
    'project_lead',
    'project_partnership',
    'software_developers',
    'directors',
    'contributors',
]


def get_year_list_from_activity(activity):
    years = []
    return years


def get_location_list_from_activity(activity):
    locations = []
    return locations


def get_role_label(role, lang):
    return get_preflabel(role, lang=lang)


def get_user_roles(activity, username):
    return [
        role['source'].split('/')[-1]
        for role in get_user_role_dicts(activity, username)
    ]


def get_user_role_dicts(activity, username):
    roles = []
    data = activity.source_repo_data['data']
    for role_field in role_fields:
        if role_field in data:
            for contributor in data[role_field]:
                if contributor.get('source') == username and (
                    contrib_roles := contributor.get('roles')
                ):
                    for role in contrib_roles:
                        roles.append(role)
    return roles
