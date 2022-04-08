import logging

from django.utils import timezone

from api.repositories.portfolio import LANGUAGES, get_preflabel

logger = logging.getLogger(__name__)


def transform_data(data, schema):
    transformed = {
        'person': {
            'primary_details': [
                {
                    'name': '{} {}'.format(
                        data.get('first_name'), data.get('last_name')
                    ),
                    'title': data.get('position'),
                    'affiliation': data.get('affiliation'),
                    'faculty': data.get('organisational_unit'),  # LDAP department
                    'contact_details': data.get(
                        'contact_email'
                    ),  # Unsure, but can be also data.get('telephone') or 'fax'
                    'skills': data.get('skills'),
                    # 'GND, VIAF, ORCID, Recherche (user profile incl. link),'  Todo not in user preferences at the moment
                    'e-mail': data.get('email'),
                    'URL': data.get('website'),
                }
            ],
            'secondary_details': [{'bio': []}],  # TODO: to be fetched from elsewhere
            # 'list': ['list_contributors'],
            'locations': data.get('location'),  # Otherwise Pelias if not satisfactory
        }
    }
    return transformed


def update_entity_from_source_repo_data(entity):
    data = entity.source_repo_data
    entity.title = data.get('name')
    subtext = []
    # TODO: design says: add position, title here. but: where do we get that from?
    subtext.append(entity.source_repo.label_institution)
    subtext.append(data['location']['office'])
    entity.subtext = subtext

    # add skills and expertise (if there are any set)
    expertise = {}
    if skills := data.get('skills'):
        for lang in LANGUAGES:
            expertise[lang] = [skill['label'].get(lang) for skill in skills]
    entity.entitydetail.expertise = expertise

    # now assemble und update the primary_details data
    primary_details = []
    # add contact data (includes, location, e-mail, URL, and GND/VIAF and ORCID links)
    contact = {}
    # TODO: adapt after User Preferences labels are added to the vocabulary
    contact_labels = {
        'contact': {'en': 'Contact', 'de': 'Kontakt'},
        'location': {
            'en': get_preflabel('location', lang='en').capitalize(),
            'de': get_preflabel('location', lang='de').capitalize(),
        },
        'place': {'en': 'Place', 'de': 'Ort'},
        'tel': {'en': 'Tel', 'de': 'Tel'},
        'mail': {'en': 'E-mail', 'de': 'E-Mail'},
        'website': {'en': 'Website', 'de': 'Website'},
        'gnd_viaf': {'en': 'GND/VIAF', 'de': 'GND/VIAF'},
        'orcid': {'en': 'ORCID', 'de': 'ORCID'},
    }
    for lang in LANGUAGES:
        # TODO: use contact concept as soon as it is implemented in the vocabulary
        label = get_preflabel('location', lang=lang).capitalize()
        if lang == 'en':
            label = 'Contact'
        elif lang == 'de':
            label = 'Kontakt'
        contact[lang] = {
            'label': label,
            'data': [],
        }

        loc = data['location']
        contact[lang]['data'].append(
            {'label': contact_labels['location'][lang], 'value': loc['street_address']},
        )
        contact[lang]['data'].append(
            {
                'label': contact_labels['place'][lang],
                'value': f'{loc["postal_code"]} {loc["place"]}, {loc["country_or_region"]}',
            },
        )
        if email := data.get('contact_email'):
            contact[lang]['data'].append(
                {
                    'label': contact_labels['mail'][lang],
                    'value': email,
                    'url': f'mailto:{email}',
                },
            )
        # TODO: phone would be next in terms of design, but where does this come from?
        if website := data.get('website'):
            contact[lang]['data'].append(
                {
                    'label': contact_labels['website'][lang],
                    'value': website,
                    'url': website,
                },
            )
        if gnd_viaf := data.get('gnd_viaf'):
            contact[lang]['data'].append(
                {
                    'label': contact_labels['gnd_viaf'][lang],
                    'value': gnd_viaf,
                    'url': f'https://d-nb.info/gnd/{gnd_viaf}',
                }
            )
        if orcid := data.get('orcid_pid'):
            contact[lang]['data'].append(
                {
                    'label': contact_labels['orcid'][lang],
                    'value': orcid,
                    'url': f'https://orcid.org/{orcid}',
                },
            )
    primary_details.append(contact)
    entity.primary_details = primary_details
    entity.date_synced = timezone.now()
    entity.save()
