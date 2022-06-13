# Search logic

This chapter defines the _Showroom_ search logic. The first section describes how
specific search indices are generated. The next section explains defines the available
filters and what they mean, followed by a section on ranking and sorting, that
explains how your search result can be ordered. A separate section on autocomplete
defines how the two autocomplete endpoints in _Showroom_ work, and how they  can be
used to suggest search terms / filters to the user based on their input. Finally, there
is also a section on the showcase search, which is only used for authenticated users,
when they edit their showcases.

## Search base ...

### ...  for full text search

For all search filters that use a full text search, a separate text search index will
be used, that is created whenever a _ShowroomObject_ is pushed / updated. Indexing in
this context means to take certain values from the received data, and add them to a text
string, which is then stored in a separate _TextSearchIndex_ model, which is
referenced by the _ShowroomObject_. The search index string will be calculated for
every available language, so that the specific request language can be used when a
client submits a full text search request.

For activities the following data:
- title
- subtitle
- texts
- activity_type
- keywords
- contributors

Additionally, every activity that has properties set in its `data` object, will be
also indexed for certain values, based on the `indexer_mapping` defined in
_src/api/repositories/portfolio/mapping.py_.

### ... for date based search

For all search filters that use a date based search, three separate date search indices
are maintained: _DateSearchIndex_, _DateRangeSearchIndex_, and _DateRelevanceIndex_. 

After the _TextSearchIndex_ for a _ShowroomObject_ is generated, the
`search_indexer` checks the `data` object of the received activity for all relevant
dates that can be found, and adds them to the corresponding search indices.


## Available filters
- `fulltext`: is a free text search filter, that returns all entities and activities
  (and later albums) that can be found with either the person or activity free text
  search filter
- `person`: can be either a free text or an id-based filter
  - if an entity id is used this filter returns the entity and all activities in which
    this entity is mentioned in
  - if a free text is used this filter returns all entities in which the requested
    search string can be found in a fulltext search on title, id, email and search index
- `activity`: can be either a free text or an id-based filter
  - if an activity id is used this filter returns the activity with this id, all related
    activities, and entities that are mentioned in the activity
  - if a free text is used this filter returns all activities that can be found on a
    fulltext search on title, subtitle and the search index (see above for search basis
    definition)
- `institution`: limits a result set to objects only from one institutions repository
- `daterange`: returns all activities that have at least one date or date range set,
  that overlaps with the requested date range. if either the `from` or the `to` property
  of the search filter is not set, we assume the earliest or latest date we have in the
  database.
- `date`: similar to date range all activities are returned that have at least one
  date set, that overlaps with the requested date (same date, or interval with this
  date in it)
- `activity_type`: returns all activities that have set the searched type (as a
  controlled vocabulary id)
- `keyword`: returns all activities that have the searched keyword set in the
  activity's keyword property (as a controlled vocabulary keyword; free-text keywords
  cannot be searched)
- `showroom_type`: returns all showroom objects with a certain type. For now this
  means either activities or persons. Departments and albums have to be added as soon
  as they are implemented. Similarly, institutions can be added, once there are more
  than one institutions in a showroom instance.
- filters used for the entity search endpoint:
  - if the search endpoint is used **without a filter**, all activities (and later
    albums) will be returned, which belong to this entity (and later also which have
    been imported by the entity's user)
  - the following filters are also available for the entity search endpoint and work
    similar to the general search filters, but limited to the objects belonging to this
    entity:
    - `fulltext`
    - `date`
    - `daterange`
    - `activity_type`
    - `keyword`
    - `activity` (works similar to the general activity, but leaves out any other
      entities that are mentioned in the activities)

While there is a general `/filters` endpoint supplying information for all available
filters, the entity page can use a separate `/entities/{id}/filters` endpoint to
retrieve filters available for the entity search (which differ primarily in the
available controlled vocabulary objects, e.g. used for keyword and type filters, because
they are solely based on the entity's activities)


## Ranking and sorting

Every search request has optional `limit` and `offset` parameters to paginate the
results. Additionally, there is:

- an `order_by` parameter, which defines the ordering/ranking and can be the following
  - `currentness`: orders all objects by date: with activities with the current date
    first, then activities with a future date, then past those with a past date
    (limited by configurable parameter)
  - `rank`: orders objects by full text search ranking (if available)
  - `default`: applies a default ordering coming from the database query. has the same
    effect as leaving out the order_by parameter as a whole


## Autocomplete

For auto completion of search strings, there are two endpoints:

- `/autocomplete/` for generic auto completions
- `/entities/{id/autocomplete/` for auto completion based on an entity's showroom
  objects

Both endpoints allow for three parameters:

- `q`: (mandatory) A string used to search all object titles (case insensitively) to
  get auto completes
- `filter_id`: (optional, defaults to "activity") can be either "default", "activity",
  or "person", to limit the queryset on which the string search with q is done. default
  does not limit the basic queryset at all, activity limits to showroom objects of type
  activity, and person to showroom objects of type person.
- `limit`: (optional) a limit to the number of results that should be returned

The autocomplete result is structured into a list of autocomplete results, each for a
different type of search filter that can be used. It is important to note, that the
filter_id used as a request parameter is technically not related to the filter_id
returned in the events. E.g. if an autocomplete request with a fulltext filter_id is
used, the results might be split into a set with filter_id activity (and a label of
"Activities") as well as a set with a filter_id person (with a label of "Person").
There is not real auto completion for full text searches, as one might be familiar with
from other search engines. In Showroom, auto complete items are only used in id-based
search filters.


## Showcase search

All search activities needed for the editing of an entity's showcase are handled through
a separate `/showcase_search` with its own parameters, separate from the above search
filters.

Parameters for this endpoint:

- `entity_id`: returns all activities
  - belonging to this entity in case of a person entity
  - imported by this institution's repository in case of an institution
  - tbd in case of a department
- `q`: returns all activities found in a full text search on activities (later: all
  types defined by `return_type`) based on the fields title, subtitle and the search
  index. this filter is based either on all activities in this showroom, or on a result
  set limited by entity_id
- optional parameter is `exclude` as a list of object ids that should not be included
  in the search result `sort`:
  - A-Z
  - Z-A
  - Modified?
- `limit` and `offset` to paginate the results
- for a future version: `return_type`
