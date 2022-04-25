import logging

from django.utils import timezone

from api.repositories.portfolio import LANGUAGES

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
    if data.get('organisational_unit'):
        subtext.append(data['organisational_unit'])
    entity.subtext = subtext

    # add skills and expertise (if there are any set)
    expertise = {}
    if skills := data.get('skills'):
        for lang in LANGUAGES:
            expertise[lang] = [skill['label'].get(lang) for skill in skills]
    entity.entitydetail.expertise = expertise

    entity.entitydetail.photo = data.get('image')

    entity.entitydetail.save()

    # now assemble und update the primary_details data
    primary_details = []

    # TODO: adapt after User Preferences labels are added to the vocabulary
    labels = {
        'contact': {'en': 'Contact', 'de': 'Kontakt'},
        'location': {'en': 'Address', 'de': 'Adresse'},
        'telephone': {'en': 'Telephone', 'de': 'Telefon'},
        'mail': {'en': 'E-mail', 'de': 'E-Mail'},
        'complementary_email': {
            'en': 'E-Mail (complementary)',
            'de': 'E-Mail (ergänzend)',
        },
        'website': {'en': 'Website', 'de': 'Website'},
        'gnd_viaf': {'en': 'GND/VIAF', 'de': 'GND/VIAF'},
        'orcid': {'en': 'ORCID', 'de': 'ORCID'},
    }

    if loc := data.get('location'):
        address = {}
        for lang in LANGUAGES:
            address[lang] = {
                'label': labels['location'],
                'data': [
                    loc['street_address'],
                    f'{loc["postal_code"]} {loc["place"]}'.strip(),
                ],
            }
        primary_details.append(address)

    contact = {}

    for lang in LANGUAGES:
        contact[lang] = {
            'label': labels['contact'],
            'data': [],
        }

        if email := data.get('email'):
            contact[lang]['data'].append(
                {
                    'label': labels['mail'][lang],
                    'value': email,
                    'url': f'mailto:{email}',
                },
            )
        if complementary_email := data.get('complementary_email'):
            contact[lang]['data'].append(
                {
                    'label': labels['complementary_email'][lang],
                    'value': complementary_email,
                    'url': f'mailto:{complementary_email}',
                },
            )
        if telephone := data.get('telephone'):
            contact[lang]['data'].append(
                {
                    'label': labels['telephone'][lang],
                    'value': telephone,
                },
            )
        if website := data.get('website'):
            contact[lang]['data'].append(
                {
                    'label': labels['website'][lang],
                    'value': website,
                    'url': website,
                },
            )
        if gnd_viaf := data.get('gnd_viaf'):
            contact[lang]['data'].append(
                {
                    'label': labels['gnd_viaf'][lang],
                    'value': gnd_viaf,
                    'url': f'https://d-nb.info/gnd/{gnd_viaf}',
                }
            )
        if orcid := data.get('orcid_pid'):
            contact[lang]['data'].append(
                {
                    'label': labels['orcid'][lang],
                    'value': orcid,
                    'url': f'https://orcid.org/{orcid}',
                },
            )
    primary_details.append(contact)
    entity.primary_details = primary_details

    entity.active = False
    if user_settings := data.get('settings'):
        if showroom := user_settings.get('showroom'):
            if activate_profile := showroom.get('activate_profile'):
                entity.active = activate_profile

    entity.date_synced = timezone.now()
    entity.save()

    if not entity.active:
        entity.deactivate()
