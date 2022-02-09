from django.conf import settings

from api.repositories.portfolio import get_altlabel_collection, get_collection_members

base_url = f'{settings.TAX_GRAPH}collection_'

list_collections = [
    'document_publication',
    'research_project',
    'awards_and_grants',
    'fellowship_visiting_affiliation',
    'exhibition',
    'teaching',
    'conference_symposium',
    'conference_contribution',
    'architecture',
    'audio',
    'concert',
    'design',
    'education_qualification',
    'functions_practice',
    'festival',
    'image',
    'performance',
    'science_to_public',
    'sculpture',
    'software',
    'film_video',
    'general_activity',
]

sub_collections = {
    'document_publication': [
        'monograph',
        'composite_volume',
        'article',
        'chapter',
        'review',
        'general_document_publication',
    ],
    'teaching': [
        'supervision_of_theses',
        'teaching',
    ],
    'functions_practice': [
        'membership',
        'expert_function',
        'journalistic_activity',
    ],
    'science_to_public': [
        'public_appearance',
        'mediation',
        'visual_verbal_presentation',
        'general_activity_science_to_public',
    ],
}

auxiliary_taxonomies = {
    'general_function_and_practice': 'http://base.uni-ak.ac.at/portfolio/taxonomy/general_function_and_practice',
}

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


def get_data_contains_filters(username):
    return [{field: [{'source': username}]} for field in role_fields]


def get_user_roles(activity, username):
    roles = []
    data = activity.source_repo_data['data']
    for role_field in role_fields:
        if role_field in data:
            for contributor in data[role_field]:
                if contributor.get('source') == username and (
                    contrib_roles := contributor.get('roles')
                ):
                    for role in contrib_roles:
                        roles.append(role['source'].split('/')[-1])
    return roles


def render_list_from_activities(activities, ordering, username):
    types = {
        collection: get_collection_members(f'{base_url}{collection}')
        for collection in list_collections
    }
    labels = {
        lang: {
            collection: get_altlabel_collection(f'collection_{collection}', lang=lang)
            for collection in list_collections
        }
        for (lang, _ll) in settings.LANGUAGES
    }
    sub_types = {
        sub: {
            collection: get_collection_members(f'{base_url}{collection}')
            for collection in sub_collections[sub]
        }
        for sub in sub_collections
    }
    sub_labels = {
        lang: {
            sub: {
                collection: get_altlabel_collection(
                    f'collection_{collection}', lang=lang
                )
                for collection in sub_collections[sub]
            }
            for sub in sub_collections
        }
        for (lang, _ll) in settings.LANGUAGES
    }

    activity_list = {
        collection: (
            []
            if collection not in sub_collections
            else {sub: [] for sub in sub_collections[collection]}
        )
        for collection in list_collections
    }
    for activity in activities:
        typ = activity.type.get('source')
        roles = get_user_roles(activity, username)

        if (
            typ in types['document_publication']
            and typ not in types['science_to_public']
            and typ not in sub_types['functions_practice']['journalistic_activity']
        ):
            if (
                typ in sub_types['document_publication']['monograph']
                and 'author' in roles
            ):
                activity_list['document_publication']['monograph'].append(activity)
            if typ in sub_types['document_publication']['composite_volume'] and (
                'editor' in roles or 'series_and_journal_editorship' in roles
            ):
                activity_list['document_publication']['composite_volume'].append(
                    activity
                )

    ret = {
        collection: {
            lang: {
                'label': labels[lang][collection],
                'data': [],
            }
            for (lang, _ll) in settings.LANGUAGES
        }
        for collection in list_collections
    }
    for collection in activity_list:
        if type(activity_list[collection]) == list:
            for (lang, _ll) in settings.LANGUAGES:
                ret[collection][lang]['data'] = [
                    render_activity(activity, lang)
                    for activity in activity_list[collection]
                ]
        else:

            for (lang, _ll) in settings.LANGUAGES:
                for sub_col in activity_list[collection]:
                    data = [
                        render_activity(activity, lang)
                        for activity in activity_list[collection][sub_col]
                    ]
                    if data:
                        ret[collection][lang]['data'].append(
                            {
                                'label': sub_labels[lang][collection][sub_col],
                                'data': data,
                            }
                        )

    return ret


def render_activity(activity, lang):
    """Render an Activity into a CommonList item."""
    subtitle = '. '.join(activity.subtext) if activity.subtext else ''
    typ = activity.type['label'].get(lang)
    # TODO: gather details from source_repo_data
    role_location_year = []
    # The output format: [title]. [subtitle] ([type]). ([role]), [location], [year]
    ret = {
        'value': f'{activity.title}.',
        'source': activity.id,
        'attributes': [
            f'{subtitle}({typ}).',
            ', '.join(role_location_year),
        ],
    }
    return ret
