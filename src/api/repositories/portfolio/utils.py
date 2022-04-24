from datetime import datetime
from typing import List

from django.conf import settings

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
    data = activity.source_repo_data['data']
    date_fields = [key for key in data if 'date' in key]
    years = []
    for fld in date_fields:
        if fld == 'date':
            years.append(year_from_date_string(data[fld]))
        elif fld in ['date_location', 'date_location_description']:
            for d in data[fld]:
                if v := d.get('date'):
                    years.append(year_from_date_string(v))
        elif fld == 'date_time_range_location':
            for d in data[fld]:
                if v := d.get('date', {}).get('date'):
                    years.append(year_from_date_string(v))
        elif fld == 'date_range':
            years.extend(years_list_from_date_range(data[fld]))
        elif fld in [
            'date_opening_location',
            'date_range_location',
            'date_range_time_range_location',
        ]:
            for d in data[fld]:
                if v := d.get('date'):
                    years.extend(years_list_from_date_range(v))
    years = sorted(set(years), reverse=True)
    return years


def get_location_list_from_activity(activity):
    data = activity.source_repo_data['data']
    location_fields = [key for key in data if 'location' in key]
    locations = []
    for fld in location_fields:
        if data.get(fld):
            if fld == 'location':
                for loc in data[fld]:
                    if loc.get('label'):
                        locations.append(loc['label'])
            else:
                for o in data[fld]:
                    if o.get('location'):
                        for loc in o['location']:
                            if loc.get('label'):
                                locations.append(loc['label'])
    if locations:
        return sorted(set(locations))
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
                if contributor.get('source') == username:
                    if contrib_roles := contributor.get('roles'):
                        for role in contrib_roles:
                            roles.append(role)
                    else:
                        # if the user has added themself as contributor without
                        # explicitly assigning a role, we'll use the contributor role
                        roles.append({'source': f'{settings.VOC_GRAPH}contributor'})
    return roles


def year_from_date_string(dt: str) -> str:
    return str(datetime.strptime(dt[:4], '%Y').year)


def years_list_from_date_range(dr) -> List[str]:
    years = []
    if dr.get('date_from') and dr.get('date_to'):
        date_from = year_from_date_string(dr['date_from'])
        date_to = year_from_date_string(dr['date_to'])
        for y in range(int(date_from), int(date_to) + 1):
            years.append(str(y))
    elif dr.get('date_from'):
        years.append(year_from_date_string(dr['date_from']))
    elif dr.get('date_to'):
        years.append(year_from_date_string(dr['date_to']))
    return years
