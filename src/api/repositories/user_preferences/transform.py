import logging

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
