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


def get_data_contains_filters(username):
    return [
        {'architecture': [{'source': username}]},
        {'authors': [{'source': username}]},
        {'artists': [{'source': username}]},
        {'winners': [{'source': username}]},
        {'granted_by': [{'source': username}]},
        {'jury': [{'source': username}]},
        {'music': [{'source': username}]},
        {'conductors': [{'source': username}]},
        {'composition': [{'source': username}]},
        {'organisers': [{'source': username}]},
        {'lecturers': [{'source': username}]},
        {'design': [{'source': username}]},
        {'commissions': [{'source': username}]},
        {'editors': [{'source': username}]},
        {'publishers': [{'source': username}]},
        {'curators': [{'source': username}]},
        {'fellow_scholar': [{'source': username}]},
        {'funding': [{'source': username}]},
        {'organisations': [{'source': username}]},
        {'project_lead': [{'source': username}]},
        {'project_partnership': [{'source': username}]},
        {'software_developers': [{'source': username}]},
        {'directors': [{'source': username}]},
        {'contributors': [{'source': username}]},
    ]


def render_list_from_activities(activities, ordering, username):
    list_collection_types = {
        collection: get_collection_members(f'{base_url}{collection}')
        for collection in list_collections
    }
    list_collection_labels = {
        lang: {
            collection: get_altlabel_collection(f'collection_{collection}', lang=lang)
            for collection in list_collections
        }
        for (lang, _ll) in settings.LANGUAGES
    }
    sub_collection_types = {
        sub: {
            collection: get_collection_members(f'{base_url}{collection}')
            for collection in sub_collections[sub]
        }
        for sub in sub_collections
    }
    sub_collection_labels = {
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
        activity_type = activity.type.get('source')

        if (
            activity_type in list_collection_types['document_publication']
            and activity_type not in list_collection_types['science_to_public']
            and activity_type
            not in sub_collection_types['functions_practice']['journalistic_activity']
        ):
            if (
                activity_type
                in sub_collection_types['document_publication']['monograph']
                and 'authors' in activity.source_repo_data['data']
                and any(
                    'source' in i and i['source'] == username
                    for i in activity.source_repo_data['data']['authors']
                )
            ):
                activity_list['document_publication']['monograph'].append(activity)

    ret = {
        collection: {
            lang: {
                'label': list_collection_labels[lang][collection],
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
                                'label': sub_collection_labels[lang][collection][
                                    sub_col
                                ],
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
