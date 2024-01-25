from django.conf import settings
from django.db.models import F
from django.db.models.functions import Greatest

from api.repositories.portfolio import get_altlabel_collection, get_collection_members
from api.repositories.portfolio.utils import (
    get_location_list_from_activity,
    get_role_label,
    get_user_roles,
    get_year_list_from_activity,
    role_fields,
)

base_url = f'{settings.TAX_GRAPH}collection_'

list_collections = [
    'document_publication',
    'research_project',
    'awards_and_grants',
    'fellowship_visiting_affiliation',
    'exhibition',
    'teaching',
    'conference',  # used for logic, while next collection ...
    'conference_symposium',  # ... is only used for the label
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
        'event',
        'membership',
        'expert_function',
        'journalistic_activity',
        'general_function_and_practice',
    ],
    'science_to_public': [
        'public_appearance',
        'mediation',
        'visual_verbal_presentation',
        'general_activity_science_to_public',
    ],
}


def get_data_contains_filters(username):
    return [{field: [{'source': username}]} for field in role_fields]


def render_list_from_activities(activities, username):
    """Return a dict in LocalisedCommonList format based on Portfolio's list
    logic.

    An entity's activity list is generated from all activities that are
    associated with an entity, where the entity has a significant role.
    The logic how this list has to be generated is documented in the
    Portfolio backend docs section on
    [lists logic](https://portfolio-backend.readthedocs.io/en/latest/lists_logic.html)
    """
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
    # general function and practice is an exception and not prefixed with collection_
    sub_types['functions_practice'][
        'general_function_and_practice'
    ] = get_collection_members(f'{settings.TAX_GRAPH}general_function_and_practice')
    for lang, _ll in settings.LANGUAGES:
        sub_labels[lang]['functions_practice'][
            'general_function_and_practice'
        ] = get_altlabel_collection('general_function_and_practice', lang=lang)
    # TODO: discuss if we should cache the above dicts for even more performance,
    #       although get_collection_members and get_altlabel_collection are cached

    activity_list = {
        collection: (
            []
            if collection not in sub_collections
            else {sub: [] for sub in sub_collections[collection]}
        )
        for collection in list_collections
    }

    # order activities by date, but creates duplicates
    activities = activities.annotate(
        order_date=Greatest(
            'datesearchindex__date',
            'daterangesearchindex__date_from',
            'daterangesearchindex__date_to',
        )
    ).order_by(F('order_date').desc(nulls_last=True))

    # because of duplictes, we need to keep track if we already
    # processed an activity
    done = []

    for activity in activities:
        if activity.id in done:
            continue
        else:
            done.append(activity.id)

        typ = activity.activitydetail.activity_type.get('source')
        typ_short = typ.split('/')[-1]
        roles = get_user_roles(activity, username)

        # 1. documents/publications
        if (
            typ not in types['science_to_public']
            and typ not in sub_types['functions_practice']['journalistic_activity']
        ):
            # - monographs
            if (
                typ in sub_types['document_publication']['monograph']
                and 'author' in roles
            ):
                activity_list['document_publication']['monograph'].append(activity)
            # - edited books
            if typ in sub_types['document_publication']['composite_volume'] and (
                'editor' in roles or 'series_and_journal_editorship' in roles
            ):
                activity_list['document_publication']['composite_volume'].append(
                    activity
                )
            # - articles
            if (
                typ in sub_types['document_publication']['article']
                and 'author' in roles
            ):
                activity_list['document_publication']['article'].append(activity)
            # - chapters
            if (
                typ in sub_types['document_publication']['chapter']
                and 'author' in roles
            ):
                activity_list['document_publication']['chapter'].append(activity)
            # - reviews
            if typ in sub_types['document_publication']['review'] and 'author' in roles:
                activity_list['document_publication']['review'].append(activity)
            # - general documents/publications
            if (
                typ in types['document_publication']
                and activity not in activity_list['document_publication']['monograph']
                and activity
                not in activity_list['document_publication']['composite_volume']
                and activity not in activity_list['document_publication']['article']
                and activity not in activity_list['document_publication']['chapter']
                and activity not in activity_list['document_publication']['review']
                and len(roles) > 0
                and 'supervisor' not in roles
            ):
                activity_list['document_publication'][
                    'general_document_publication'
                ].append(activity)
        # 2. research and projects
        if (
            typ in types['research_project']
            and len(roles) > 0
            and ('teaching_project_teaching_research_project' not in roles)
        ):
            activity_list['research_project'].append(activity)
        # 3. awards and grants
        if typ in types['awards_and_grants'] and len(roles) > 0:
            activity_list['awards_and_grants'].append(activity)
        # 4. fellowships and visiting affiliations
        if typ in types['fellowship_visiting_affiliation'] and len(roles) > 0:
            activity_list['fellowship_visiting_affiliation'].append(activity)
        # 5. exhibitions
        if (
            typ in types['exhibition']
            and len(roles) > 0
            and (typ not in types['science_to_public'])
        ):
            activity_list['exhibition'].append(activity)
        # 6. teaching
        #   - supervision of theses
        if typ in sub_types['teaching']['supervision_of_theses'] and (
            'expertizing' in roles or 'supervisor' in roles
        ):
            activity_list['teaching']['supervision_of_theses'].append(activity)
        #   - teaching
        if (
            typ in sub_types['teaching']['teaching']
            or typ in types['education_qualification']
        ) and 'lecturer' in roles:
            activity_list['teaching']['teaching'].append(activity)
        # 7. conferences & symposia
        if (
            typ in types['conference']
            and len(roles) > 0
            and (
                typ not in types['science_to_public']
                and typ not in sub_types['functions_practice']['journalistic_activity']
                and typ not in sub_types['teaching']['teaching']
                and typ not in types['education_qualification']
            )
        ):
            activity_list['conference_symposium'].append(activity)
        # 8. conference contributions
        if (
            typ in types['conference_contribution']
            and len(roles) > 0
            and (typ not in types['science_to_public'])
        ):
            activity_list['conference_contribution'].append(activity)
        # 9. architecture
        if typ in types['architecture'] and len(roles) > 0:
            activity_list['architecture'].append(activity)
        # 10. audios
        if (
            typ in types['audio']
            and len(roles) > 0
            and (
                typ not in types['science_to_public']
                and typ not in sub_types['functions_practice']['journalistic_activity']
            )
        ):
            activity_list['audio'].append(activity)
        # 11. concerts
        if typ in types['concert'] and len(roles) > 0:
            activity_list['concert'].append(activity)
        # 12. design
        if typ in types['design'] and len(roles) > 0:
            activity_list['design'].append(activity)
        # 13. education & qualification
        if typ in types['education_qualification'] and 'attendance' in roles:
            activity_list['education_qualification'].append(activity)
        # 14. functions & practice
        if typ not in types['science_to_public']:
            # - memberships
            if typ in sub_types['functions_practice']['event'] and (
                'member' in roles
                or 'board_member' in roles
                or 'advisory_board' in roles
                or 'commissions_boards' in roles
                or 'appointment_committee' in roles
                or 'jury' in roles
                or 'chair' in roles
                or 'board_of_directors' in roles
            ):
                activity_list['functions_practice']['membership'].append(activity)
            # - expert functions
            if typ in sub_types['functions_practice']['event'] and (
                'expertizing' in roles or 'committee_work' in roles
            ):
                activity_list['functions_practice']['expert_function'].append(activity)
            # - journalistic activities
            if typ in sub_types['functions_practice']['journalistic_activity'] and (
                'author' in roles
                or 'editing' in roles
                or 'editor' in roles
                or 'interviewer' in roles
                or 'photography' in roles
                or 'speaker' in roles
                or 'moderation' in roles
            ):
                activity_list['functions_practice']['journalistic_activity'].append(
                    activity
                )
            # - general functions & practice
            if (
                typ in sub_types['functions_practice']['event']
                and activity not in activity_list['functions_practice']['membership']
                and activity
                not in activity_list['functions_practice']['expert_function']
                and activity
                not in activity_list['functions_practice']['journalistic_activity']
                and len(roles) > 0
            ):
                activity_list['functions_practice'][
                    'general_function_and_practice'
                ].append(activity)
        # 15. festivals
        if typ in types['festival'] and len(roles) > 0:
            activity_list['festival'].append(activity)
        # 16. images
        if typ in types['image'] and len(roles) > 0:
            activity_list['image'].append(activity)
        # 17. performances
        if typ in types['performance'] and len(roles) > 0:
            activity_list['performance'].append(activity)
        # 18. science to public
        #   - public appearances
        if (
            (
                typ in sub_types['science_to_public']['public_appearance']
                and len(roles) > 0
            )
            or (
                typ_short in ['discussion', 'panel_discussion', 'roundtable', 'panel']
                and ('discussion' in roles or 'panelist' in roles)
            )
            or (
                typ_short == 'recitation'
                and (
                    'reading' in roles
                    or 'actor' in roles
                    or 'performing_artist' in roles
                    or 'artist' in roles
                    or 'performance' in roles
                    or 'presentation' in roles
                    or 'speech' in roles
                    or 'speaker' in roles
                    or 'lecturer' in roles
                )
            )
            or (
                typ_short in ['authors_presentation', 'book_presentation']
                and 'author' in roles
            )
            or (
                typ in sub_types['functions_practice']['journalistic_activity']
                and (
                    'mention' in roles
                    or 'talk' in roles
                    or 'contribution' in roles
                    or 'interviewee' in roles
                )
            )
        ):
            activity_list['science_to_public']['public_appearance'].append(activity)
        #   - mediation
        if typ in sub_types['science_to_public']['mediation'] and 'mediation' in roles:
            activity_list['science_to_public']['mediation'].append(activity)
        #   - visual and verbal presentations
        if (
            typ in sub_types['science_to_public']['visual_verbal_presentation']
            and len(roles) > 0
        ):
            activity_list['science_to_public']['visual_verbal_presentation'].append(
                activity
            )
        #   - general activities science to public
        if (
            typ in sub_types['science_to_public']['general_activity_science_to_public']
            and len(roles) > 0
        ):
            activity_list['science_to_public'][
                'general_activity_science_to_public'
            ].append(activity)
        # 19. sculptures
        if typ in types['sculpture'] and len(roles) > 0:
            activity_list['sculpture'].append(activity)
        # 20. softwares
        if typ in types['software'] and len(roles) > 0:
            activity_list['software'].append(activity)
        # 21. films/videos
        if (
            typ in types['film_video']
            and len(roles) > 0
            and (
                typ not in types['science_to_public']
                and typ not in sub_types['functions_practice']['journalistic_activity']
            )
        ):
            activity_list['film_video'].append(activity)
        # 22. general activities
        if len(roles) > 0:
            found = False
            for collection in activity_list:
                if type(activity_list[collection]) is list:
                    if activity in activity_list[collection]:
                        found = True
                else:
                    for sub_col in activity_list[collection]:
                        if activity in activity_list[collection][sub_col]:
                            found = True
            if not found:
                activity_list['general_activity'].append(activity)

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
        if type(activity_list[collection]) is list:
            for lang, _ll in settings.LANGUAGES:
                ret[collection][lang]['data'] = [
                    render_activity(activity, lang, username)
                    for activity in activity_list[collection]
                ]
        else:
            for lang, _ll in settings.LANGUAGES:
                for sub_col in activity_list[collection]:
                    data = [
                        render_activity(activity, lang, username)
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


def render_activity(activity, lang, username):
    """Render an Activity into a CommonList item."""
    subtitle = '. '.join(activity.subtext) if activity.subtext else ''
    typ = activity.activitydetail.activity_type['label'].get(lang)
    # TODO: gather details from source_repo_data
    roles = get_user_roles(activity, username)
    roles = [get_role_label(role, lang) for role in roles]
    roles = ', '.join(roles)
    roles = f'({roles})'
    location = ', '.join(get_location_list_from_activity(activity))
    year = ', '.join(get_year_list_from_activity(activity))
    role_location_year = [i for i in [roles, location, year] if i]
    # The output format: [title]. [subtitle] ([type]). ([role]), [location], [year]
    ret = {
        'value': activity.title,
        'source': activity.id,
        'attributes': [
            f'{subtitle} ({typ})',
            ', '.join(role_location_year),
        ],
    }
    return ret
