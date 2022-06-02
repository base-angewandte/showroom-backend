# API Plugins

*Showroom* follows an approach where every functionality that is particular to a certain
institutional setup (e.g. integrations for certain CMS or other systems) is provided
by configurable plugins. These are turned off by default settings. When turned on
through a corresponding setting in the `.env` file, these plugins add certain endpoints
and functionality to the core API.

Currently, there is only one API plugin called `repo_source`, which is used to retrieve
published activities from *Showroom* in the schema of the original repository, e.g.
as retrieved by *Portfolio*. This can be used e.g. to adopt existing integrations which
so far worked with entry data coming directly from the source repository.

## Restricting access through API keys

To potentially restrict access to API plugin functionality, plugins can use API keys
configurable through the Django admin interface. Every _Plugin API key_ that is
generated, can be set to expire after a defined date or be revoked manually.
Additionally, it can also be set to either active or inactive (defaults to active). Its
use can also be restricted to certain plugins and clients with only certain IP
addresses.

This is currently represented as a simple text field in the Django admin, which should
contain valid JSON data. The default list of IPs is `["*"]`, so a list with one entry,
the `*` which can be used to allow access from any IP. Instead of this `*` the list can
contain valid IPv4 and IPv6 addresses.

The list of plugins is also a JSON list, containing string representation of the plugins
this key is allowed to use. The description will list all available and activated
plugins.

Clients using an API key, have to send the key in the HTTP headers as follows:
```
Authorization: Api-Key <key>
```

## The `repo_source` plugin

This plugin adds an authenticated `GET /api/v1/activites/{id}/repo-source/` endpoint,
which provides the data *Showroom* has received from the repository when it pushed the
activity to *Showroom*. This does not necessarily contain all date from the entry in
the source repository (as e.g. notes in *Portfolio* are never published), but it
represents the activity in the original form, also containing the original concept
URIs and contributor source IDs.

To authenticate for this endpoint a client needs a valid Plugin API key.

Additional to the original data from the repository, Showroom will add certain
properties, which either do not make sense in the original format, or are only available
post publication in *Showroom*, e.g. ID of the activity in *Showroom*, or the publishing
info containing times of first and updated publishing, and the *Showroom* entity
publishing the activity (if they have activated their *Showroom* page, otherwise only
the original user id from the repo will be set). These properties will be added to the
response data with a `_` prefix to the property name, e.g. `_publishing_info`.

The `_relations` are presented not as in the original repository, but with their
*Showroom* activity IDs, as only these can be used to retrieve those other activities.

In order to map contributor IDs from the source repository data, to *Showroom* entities
with activated user page, a `_entity_mapping` property is added to the response data.
