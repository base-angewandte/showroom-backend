# Data transformation definitions

This section contains the detailed mapping of repository data to ShowroomObject fields.
See the _Details on how to transform data_ section in [](./architecture.md) for context
and a general explanation on data transformations ins _Showroom_.

## person

A ShowroomObject of the type person (usually pushed/pulled from the user repository).

- `title` contains:
  - name, surname
- `subtext` contains:
  - position, title
- `pimary_details` contains:
  - affiliation
  - faculty
  - contact details
  - skills and expertise
  - GND, VIAF, ORCID
  - e-mail
  - website
- `secondary_details` contains:
  - short biography
- `list` contains:
  - all the person's activities, based on the [](./lists_logic.md)
- `location` contains:
  - the person's office address

## \_\_none\_\_

If the type is not set in the entry, or if it is a type that cannot be linked to any of
the following concepts.

- `title` contains:
  - title
- `subtext` contains:
  - subtitle
- `primary_details` contains:
  - keywords
- `secondary_details` contains:
  - texts with types
- `list` stays empty
- `location` stays empty

## architecture

Includes all entries belonging to a type listed in the
[collection_architecture](http://base.uni-ak.ac.at/portfolio/taxonomy/collection_architecture)
concept.

- `title` contains:
  - title
- `subtext` contains:
  - subtitle
- `primary_details` contains:
  - architecture
  - date, location, location description
  - keywords
  - url
- `secondary_details` contains:
  - texts with types
  - material, format
  - dimensions
- `list` contains:
  - contributors
- `location` contains:
  - all locations found in the entry

## audio

Includes all entries belonging to a type listed in the
[collection_audio](http://base.uni-ak.ac.at/portfolio/taxonomy/collection_audio)
concept.

- `title` contains:
  - title
- `subtext` contains:
  - subtitle
- `primary_details` contains:
  - authors
  - artists
  - date, location, location description
  - keywords
  - url
- `secondary_details` contains:
  - texts with types
  - material, format
  - duration
  - language
- `list` contains:
  - contributors
  - published in
- `location` should not be displayed for this type of activity

## awards and grants

Includes all entries belonging to a type listed in the
[collection_awards_and_grants](http://base.uni-ak.ac.at/portfolio/taxonomy/collection_awards_and_grants)
concept.

- `title` contains:
  - title
- `subtext` contains:
  - subtitle
- `primary_details` contains:
  - winners
  - granted by
  - award date
  - keywords
  - url
- `secondary_details` contains:
  - texts with types
  - category
  - jury
  - arward ceremony, location, location description
- `list` contains:
  - contributors
- `location` contains:
  - all locations found in the entry

## concert

Includes all entries belonging to a type listed in the
[collection_concert](http://base.uni-ak.ac.at/portfolio/taxonomy/collection_concert)
concept.

- `title` contains:
  - title
- `subtext` contains:
  - subtitle
- `primary_details` contains:
  - music
  - composition
  - date, time, location, location description
  - keywords
  - url
- `secondary_details` contains:
  - texts with types
  - conductors
  - opening
- `list` contains:
  - contributors
- `location` contains:
  - all locations found in the entry

## conference

Includes all entries belonging to a type listed in the
[collection_conference](http://base.uni-ak.ac.at/portfolio/taxonomy/collection_conference)
concept.

- `title` contains:
  - title
- `subtext` contains:
  - subtitle
- `primary_details` contains:
  - organisers
  - date, time, location, location description
  - keywords
  - url
- `secondary_details` contains:
  - texts with types
  - lecturers
- `list` contains:
  - contributors
- `location` contains:
  - all locations found in the entry

## conference contribution

Includes all entries belonging to a type listed in the
[collection_conference_contribution](http://base.uni-ak.ac.at/portfolio/taxonomy/collection_conference_contribution)
concept.

- `title` contains:
  - title
- `subtext` contains:
  - subtitle
- `primary_details` contains:
  - lecturers
  - date, time, location, location description
  - keywords
  - url
- `secondary_details` contains:
  - texts with types
  - title of event
  - organisers
- `list` contains:
  - contributors
- `location` contains:
  - all locations found in the entry

## design

Includes all entries belonging to a type listed in the
[collection\_](http://base.uni-ak.ac.at/portfolio/taxonomy/collection_)
concept.

- `title` contains:
  - title
- `subtext` contains:
  - subtitle
- `primary_details` contains:
  - design
  - date, location, location description
  - keywords
  - url
- `secondary_details` contains:
  - commissions
  - texts with types
  - material, format
- `list` contains:
  - contributors
- `location` should not be displayed for this type of activity

## document/publication

Includes all entries belonging to a type listed in the
[collection_document_publication](http://base.uni-ak.ac.at/portfolio/taxonomy/collection_document_publication)
concept.

- `title` contains:
  - title
- `subtext` contains:
  - subtitle
- `pimary_details` contains:
  - type
  - authors
  - editors
  - publisher, place, date
  - keywords
  - ISBN, DOI
  - url
- `secondary_details` contains:
  - texts with types
  - volume/issue, pages
  - language, format, material, edition
- `list` contains:
  - published in
  - contributors
- `location` should not be displayed for this type of activity

## event

Includes all entries belonging to a type listed in the
[collection_event](http://base.uni-ak.ac.at/portfolio/taxonomy/collection_event)
concept.

- `title` contains:
  - title
- `subtext` contains:
  - subtitle
- `primary_details` contains:
  - date, time, location, location description
  - keywords
  - url
- `secondary_details` contains:
  - texts with types
- `list` contains:
  - contributors
- `location` contains:
  - all locations found in the entry

## exhibition

Includes all entries belonging to a type listed in the
[collection_exhibition](http://base.uni-ak.ac.at/portfolio/taxonomy/collection_exhibition)
concept.

- `title` contains:
  - title
- `subtext` contains:
  - subtitle
- `primary_details` contains:
  - artists
  - curators
  - opening date, location
  - keywords
  - url
- `secondary_details` contains:
  - texts with types
  - opening
- `list` contains:
  - contributors
- `location` contains:
  - all locations found in the entry

## fellowship and visiting affiliation

Includes all entries belonging to a type listed in the
[collection_fellowship_visiting_affiliation](http://base.uni-ak.ac.at/portfolio/taxonomy/collection_fellowship_visiting_affiliation)
concept.

- `title` contains:
  - title
- `subtext` contains:
  - subtitle
- `primary_details` contains:
  - fellow
  - date range, location
  - keywords
  - url
- `secondary_details` contains:
  - commissions
  - funding
  - organisations
  - texts with types
- `list` contains:
  - contributors
- `location` contains:
  - all locations found in the entry

## festival

Includes all entries belonging to a type listed in the
[collection_festival](http://base.uni-ak.ac.at/portfolio/taxonomy/collection_festival)
concept.

- `title` contains:
  - title
- `subtext` contains:
  - subtitle
- `primary_details` contains:
  - artists
  - curators
  - date, time, location, location description
  - keywords
  - url
- `secondary_details` contains:
  - texts with types
  - organisers
- `list` contains:
  - contributors
- `location` contains:
  - all locations found in the entry

## film / video

Includes all entries belonging to a type listed in the
[collection\_](http://base.uni-ak.ac.at/portfolio/taxonomy/collection_)
concept.

- `title` contains:
  - title
- `subtext` contains:
  - subtitle
- `primary_details` contains:
  - directors
  - date, location, location description
  - keywords
  - url
- `secondary_details` contains:
  - texts with types
  - isan
  - material, format
  - duration
  - language
- `list` contains:
  - contributors
  - published in
- `location` should not be displayed for this type of activity

## image

Includes all entries belonging to a type listed in the
[collection\_](http://base.uni-ak.ac.at/portfolio/taxonomy/collection_)
concept.

- `title` contains:
  - title
- `subtext` contains:
  - subtitle
- `primary_details` contains:
  - artists
  - date, location, location description
  - keywords
  - url
- `secondary_details` contains:
  - texts with types
  - material, format, dimensions
- `list` contains:
  - contributors
- `location` contains:
  - all locations found in the entry

## performance

Includes all entries belonging to a type listed in the
[collection_performance](http://base.uni-ak.ac.at/portfolio/taxonomy/collection_performance)
concept.

- `title` contains:
  - title
- `subtext` contains:
  - subtitle
- `primary_details` contains:
  - artists
  - date, time, location, location description
  - keywords
  - url
- `secondary_details` contains:
  - texts with types
  - material
  - format
- `list` contains:
  - contributors
- `location` contains:
  - all locations found in the entry

## research project

Includes all entries belonging to a type listed in the
[collection_research_project](http://base.uni-ak.ac.at/portfolio/taxonomy/collection_research_project)
concept.

- `title` contains:
  - title
- `subtext` contains:
  - subtitle
- `primary_details` contains:
  - project lead
  - project partners
  - date range
  - keywords
  - url
- `secondary_details` contains:
  - texts with types
  - funding
  - funding category
  - status
- `list` contains:
  - contributors
- `location` should not be displayed for this type of activity

## sculpture

Includes all entries belonging to a type listed in the
[collection_sculpture](http://base.uni-ak.ac.at/portfolio/taxonomy/collection_sculpture)
concept.

- `title` contains:
  - title
- `subtext` contains:
  - subtitle
- `primary_details` contains:
  - artists
  - date, location, location description
  - keywords
  - url
- `secondary_details` contains:
  - texts with types
  - material, format
  - dimensions
- `list` contains:
  - contributors
- `location` contains:
  - all locations found in the entry

## software

Includes all entries belonging to a type listed in the
[collection_software](http://base.uni-ak.ac.at/portfolio/taxonomy/collection_software)
concept.

- `title` contains:
  - title
- `subtext` contains:
  - subtitle
- `primary_details` contains:
  - software developers
  - date
  - open source license
  - keywords
  - url
- `secondary_details` contains:
  - texts with types
  - programming language
  - git url
  - documentation url
  - software version
- `list` contains:
  - contributors
- `location` should not be displayed for this type of activity
