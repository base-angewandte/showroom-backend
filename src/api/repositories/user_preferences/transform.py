import logging
from datetime import datetime

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
    # TODO: add position, title
    subtext.append(entity.source_repo.label_institution)
    # TODO: add department
    entity.subtext = subtext

    # now assemble und update the primary_field data
    # TODO: contact details (address from LDAP)
    # TODO: skills and expertise
    # TODO: GND, VIAF, ORCID, Recherche (user profile incl. link)
    # TODO: e-mail
    # TODO: URL / website

    # the secondary_field only contains the bio
    # TODO: bio

    entity.date_synced = datetime.now()
    entity.save()
