# Architecture and data model

*Showroom* is part of a potential ensemble of applications, that are used to display
current art and research information from several institutions' repositories.

In its most simple setup, *Showroom* will be combined with a single *Portfolio*
instance, and a *CAS/UserPreferences* instance to provide entity data. But it could
also be used to only display the activities that are published from *Portfolio*,
without including any detailed data about the users/publishers of those activites.
In that case a single *Showroom* can be combined with a single *Portfolio* instance,
and the user repository can be disabled in the configuration.

However, *Showroom* is built in a way to accommodate different *Portfolio*
instances as repositories, and in hindsight of adding adapters for other
CRIS or object repositories in the future. This is one of the main reasons why
*Showroom* does not just mirror tha data model used in *Portfolio*.

The following subsections aim to shed some light on the architectural decisions
in this project and how data is handled and transformed.

## The basic architecture

In the following diagram you see a macro perspective on _Showroom_ and how
it is connected to other components. A detailed explanation follows below.

![Showroom Backend Architecture Diagram](showroom-backend-architecture.png)
(full-size image: [](showroom-backend-architecture.png)
drawio source: [](showroom-backend-architecture.drawio))

Let's look at the _Showroom Backend_ itself first. The data is stored in a
_PostgreSQL_ database - which in our default setup runs in its own container. The
backend itself is a _Django_ application - also running in its own container or for
development on the developers host, ideally using a python virtual environment. More
on that in the [](./install.md) section. Apart from that we are using a
_Redis_ store - also in its own container - for caching and message queueing.

The backend provides a REST API, which is described in more detail in [](./rest_api.md).
It provides public and authenticated endpoints for the frontend, as well as
endpoints with an API key based authentication for repositories to push data to
_Showroom_.

A central component of _Showroom_ is the _Portfolio adapter_, which is responsible
to handle all transformations and elaborations for entry data that is published in
_Portfolio_. It is also responsible for generating all relevant search indices, that
are used in the search. For more information on the data model see the corresponding
section below. For mode details on the search functionality go to [](./search_logic.md).

Now, apart from the _Showroom Backend_ there is of course also a _Showroom Frontend_,
which is a server-side rendered application written with Nuxt.js and Vue.js . All
display and manipulation of Showroom data for and by users is handled through the
frontend. Apart from that the backend still provides the classic Django admin for
administration and mostly development and debugging convenience.

To get actual data into _Showroom_ we need a repository, that uses the
`repo` endpoints, to push published entries. In this basic setup we hae a single
[base Portfolio](https://github.com/base-angewandte/portfolio-backend) instance
that pushes entries to Showroom, whenever they are published
by its users. Next to this repository we need an authentication backend, that
also provides information about the users/publishers - as long as they have activated
their _Showroom_ page. This can also be called the _user repository_, in our basic setup
a single instance of [base CAS](https://github.com/base-angewandte/cas) with the
_User Preferences_ module, that has been added in 1.1. While in this case there is only a single data and a single user repository, there
could be more repositories connected to Showroom. This is elaborated in the next
section.

Then there is a controlled vocabulary in form of a [Skosmos](http://www.skosmos.org/)
instance. This is used by Showroom (as well as by Portfolio) to provide localized labels
for a range of concepts described in the data.


## Ecosystem architecture

The following diagram shows the potential application of Showroom in a multi-instance
and multi-stakeholder data ecosystem.

![Showroom Ecosystem Architecture Diagram](showroom-ecosystem-architecture.drawio.png)
(full-size image: [](showroom-ecosystem-architecture.drawio.png)
drawio source: [](showroom-ecosystem-architecture.drawio))


In contrast to what we have seen in the former section on the basic architecture,
here we see how different repositories are connected to a _Showroom Backend_ instance,
who can all push data, that was published by their users. While currently this is
already possible with different _Portfolio_ instances, the adoption of different
CRIS or other data repositories would require the development of a corresponding
adapter.

> Note: while Showroom Backend is developed with hindsight to other potential repo
> adapters, currently we still would need to refactor some significant parts of the
> backend code, to have a fully modularized version, where repo adapters can be
> interchanged by a mere configuration directive and the use of a corresponding module.

Similar to several data repositories, Showroom could also accommodate for different
user repositories / authentication backends. Similar to the idea of repo adapters, this
is still an abstract concept and would require implementation in a later version.

The user in the end should be able to access a _Showroom_ instance through different
frontends. This allows for different institutions to use the same _Showroom_
infrastructure, while still providing a customized or branded user experience to its
own user base. Additionally, their can be joint platforms showcasing the activities
of several institutions in one place.


## Showroom objects, and the data model

Showroom combines data from published entries in data repositories as well as data from
user repositories, if users have activated their Showroom page. These should be
presented in similar user interface structures and also searchable in mostly similar
ways. In addition to what comes in from the repositories, it is also planned to add
albums as another type of Showroom object, which is solely maintained by the users
within Showroom. Similarly, users can already maintain their biographic data and a
showcase for their user page within Showroom.

These are the guiding considerations for the design of the Showroom data model, which
will be explained in a bit more detail in this section.

Showroom contains the following entities, implemented as Django models: 

* `SourceRepository` : a representation of an institution's repository, including the
  API key used by the repository to authenticate.
* `ShowroomObject` : any object in Showroom that can be displayed on a distinct page. So
  far this contains _entities_ (persons, departements and insitutions) and _activities_
  (the entries published in the repository). In the future _albums_ will be a different
  kind of ShowroomObject.
* `EntityDetail` : contains aggregated data only for ShowroomObjects of an _entity_ type
* `ActivityDetail` : contains aggergated data only for ShowroomObjects that are
  _activities_
* `Media` : stores metadata about media that are associated with a ShowroomObject
  (usually an activity). The media files themselves are not stored in Showroom, only
  the links to the publicly consumable media in the SourceRepository.

Further, the following (explicit) Django models are used to manage relationships
between ShowroomObjects or to create search indices:

* Relation
* ContributorActivityRelations
* TextSearchIndex
* DateSearchIndex
* DateRangeSearchIndex
* DateRelevanceIndex

The following diagram displays those core models (with a green box color), as well
as the available endpoints in the API (with a light magenta-ish box color) and all
the elaborated data formats (with a light violet box color), that are used by the
API, or by some object properties to store information. Additionally the elaborated
data formats in the diagram display the relations between actual core model data
and what the clients get through the API.

![Showroom Data Model Diagram](showroom-model-classes.png)
(full-size image: [](showroom-model-classes.png)
drawio source: [](showroom-model-classes.drawio))

What this model does not show are the transformations from an activity's source data
format in the repository (e.g. as it is stored in _Portfolio_) to how it is stored
in Showroom. This will be elaborated in the next section.

### Data transformations

When a repository pushes one of its entries to Showroom, it has to be transformed into
a _ShowroomObject_ of the type `activity`. In Showroom all published entries from
repositories are framed as activities which belong to a user, which is linked in
the activities, if they also have activated their Showroom user page. Those activities
then fall into different categories, like "document/publication", "exhibition", "audio",
"research project", or one of the many more available categories.

Depending on which category this activity falls into, it should be displayed differently
in Showroom.

While the Showroom Frontend is finally responsible for displaying the results, the
Showroom Backend is responsible for already preparing the data to be displayed, so that
that most of the needed transformations are done already on creation/update of an
activity, and the data is ready for the response, whenever a client requests the
activity.

So, while the original data from the repository will be stored on the _ShowroomObject_
in the `source_repo_data` property, the following properties should already hold the
data as it is displayed by the Showroom Frontend:

* `title`
* `subtext`
* `primary_details`
* `secondary_details`
* `list`
* `locations`

The following subsections list which of the properties from the repository data should
be transformed into which of those ShowroomObject properties, based on which category /
activity type they fall in.

Below these sections we provide a bit more detail on how those transformations are
supposed to work.

#### person

A ShowroomObject of the type person (usually pushed/pulled from the user repository).

* `title` contains:
  - name, surname
* `subtext` contains:
  - position, title
* `pimary_details` contains:
  - affiliation
  - faculty
  - contact details
  - skills and expertise
  - GND, VIAF, ORCID
  - e-mail
  - website
* `secondary_details` contains:
  - short biography
* `list` contains:
  - all the person's activities, based on the [](./lists_logic.md)
* `location` contains:
  - the person's office address

#### \_\_none\_\_

If the type is not set in the entry, or if it is a type that cannot be linked to any of
the following concepts.

* `title` contains:
    - title
* `subtext` contains:
    - subtitle
* `primary_details` contains:
    - keywords
* `secondary_details` contains:
    - texts with types
* `list` stays empty
* `location` stays empty

#### architecture

Includes all entries belonging to a type listed in the
[collection_architecture](http://base.uni-ak.ac.at/portfolio/taxonomy/collection_architecture)
concept.

* `title` contains:
    - title
* `subtext` contains:
    - subtitle
* `primary_details` contains:
    - architecture
    - date, location, location description
    - keywords
    - url
* `secondary_details` contains:
    - texts with types
    - material, format
    - dimensions
* `list` contains:
    - contributors
* `location` contains:
    - all locations found in the entry


#### audio

Includes all entries belonging to a type listed in the
[collection_audio](http://base.uni-ak.ac.at/portfolio/taxonomy/collection_audio)
concept.

* `title` contains:
    - title
* `subtext` contains:
    - subtitle
* `primary_details` contains:
    - authors
    - artists
    - date, location, location description
    - keywords
    - url
* `secondary_details` contains:
    - texts with types
    - material, format
    - duration
    - language
* `list` contains:
    - contributors
    - published in
* `location` should not be displayed for this type of activity

#### awards and grants

Includes all entries belonging to a type listed in the
[collection_awards_and_grants](http://base.uni-ak.ac.at/portfolio/taxonomy/collection_awards_and_grants)
concept.

* `title` contains:
    - title
* `subtext` contains:
    - subtitle
* `primary_details` contains:
    - winners
    - granted by
    - award date
    - keywords
    - url
* `secondary_details` contains:
    - texts with types
    - category
    - jury
    - arward ceremony, location, location description
* `list` contains:
    - contributors
* `location` contains:
    - all locations found in the entry

#### concert

Includes all entries belonging to a type listed in the
[collection_concert](http://base.uni-ak.ac.at/portfolio/taxonomy/collection_concert)
concept.

* `title` contains:
    - title
* `subtext` contains:
    - subtitle
* `primary_details` contains:
    - music
    - composition
    - date, time, location, location description
    - keywords
    - url
* `secondary_details` contains:
    - texts with types
    - conductors
    - opening
* `list` contains:
    - contributors
* `location` contains:
    - all locations found in the entry

#### conference

Includes all entries belonging to a type listed in the
[collection_conference](http://base.uni-ak.ac.at/portfolio/taxonomy/collection_conference)
concept.

* `title` contains:
    - title
* `subtext` contains:
    - subtitle
* `primary_details` contains:
    - organisers
    - date, time, location, location description
    - keywords
    - url
* `secondary_details` contains:
    - texts with types
    - lecturers
* `list` contains:
    - contributors
* `location` contains:
    - all locations found in the entry

#### conference contribution

Includes all entries belonging to a type listed in the
[collection_conference_contribution](http://base.uni-ak.ac.at/portfolio/taxonomy/collection_conference_contribution)
concept.

* `title` contains:
    - title
* `subtext` contains:
    - subtitle
* `primary_details` contains:
    - lecturers
    - date, time, location, location description
    - keywords
    - url
* `secondary_details` contains:
    - texts with types
    - title of event
    - organisers
* `list` contains:
    - contributors
* `location` contains:
    - all locations found in the entry

#### design

Includes all entries belonging to a type listed in the
[collection_](http://base.uni-ak.ac.at/portfolio/taxonomy/collection_)
concept.

* `title` contains:
    - title
* `subtext` contains:
    - subtitle
* `primary_details` contains:
    - design
    - date, location, location description
    - keywords
    - url
* `secondary_details` contains:
    - commissions
    - texts with types
    - material, format
* `list` contains:
    - contributors
* `location` should not be displayed for this type of activity

#### document/publication

Includes all entries belonging to a type listed in the
[collection_document_publication](http://base.uni-ak.ac.at/portfolio/taxonomy/collection_document_publication)
concept.

* `title` contains:
  - title
* `subtext` contains:
  - subtitle
* `pimary_details` contains:
  - type
  - authors
  - editors
  - publisher, place, date
  - keywords
  - ISBN, DOI
  - url
* `secondary_details` contains:
  - texts with types
  - volume/issue, pages
  - language, format, material, edition
* `list` contains:
  - published in
  - contributors
* `location` should not be displayed for this type of activity

#### event

Includes all entries belonging to a type listed in the
[collection_event](http://base.uni-ak.ac.at/portfolio/taxonomy/collection_event)
concept.

* `title` contains:
    - title
* `subtext` contains:
    - subtitle
* `primary_details` contains:
    - date, time, location, location description
    - keywords
    - url
* `secondary_details` contains:
    - texts with types
* `list` contains:
    - contributors
* `location` contains:
    - all locations found in the entry

#### exhibition

Includes all entries belonging to a type listed in the
[collection_exhibition](http://base.uni-ak.ac.at/portfolio/taxonomy/collection_exhibition)
concept.

* `title` contains:
    - title
* `subtext` contains:
    - subtitle
* `primary_details` contains:
    - artists
    - curators
    - opening date, location
    - keywords
    - url
* `secondary_details` contains:
    - texts with types
    - opening
* `list` contains:
    - contributors
* `location` contains:
    - all locations found in the entry

#### fellowship and visiting affiliation

Includes all entries belonging to a type listed in the
[collection_fellowship_visiting_affiliation](http://base.uni-ak.ac.at/portfolio/taxonomy/collection_fellowship_visiting_affiliation)
concept.

* `title` contains:
    - title
* `subtext` contains:
    - subtitle
* `primary_details` contains:
    - fellow
    - date range, location
    - keywords
    - url
* `secondary_details` contains:
    - commissions
    - funding
    - organisations
    - texts with types
* `list` contains:
    - contributors
* `location` contains:
    - all locations found in the entry

#### festival

Includes all entries belonging to a type listed in the
[collection_festival](http://base.uni-ak.ac.at/portfolio/taxonomy/collection_festival)
concept.

* `title` contains:
    - title
* `subtext` contains:
    - subtitle
* `primary_details` contains:
    - artists
    - curators
    - date, time, location, location description
    - keywords
    - url
* `secondary_details` contains:
    - texts with types
    - organisers
* `list` contains:
    - contributors
* `location` contains:
    - all locations found in the entry

#### film / video

Includes all entries belonging to a type listed in the
[collection_](http://base.uni-ak.ac.at/portfolio/taxonomy/collection_)
concept.

* `title` contains:
    - title
* `subtext` contains:
    - subtitle
* `primary_details` contains:
    - directors
    - date, location, location description
    - keywords
    - url
* `secondary_details` contains:
    - texts with types
    - isan
    - material, format
    - duration
    - language
* `list` contains:
    - contributors
    - published in
* `location` should not be displayed for this type of activity

#### image

Includes all entries belonging to a type listed in the
[collection_](http://base.uni-ak.ac.at/portfolio/taxonomy/collection_)
concept.

* `title` contains:
    - title
* `subtext` contains:
    - subtitle
* `primary_details` contains:
    - artists
    - date, location, location description
    - keywords
    - url
* `secondary_details` contains:
    - texts with types
    - material, format, dimensions
* `list` contains:
    - contributors
* `location` contains:
    - all locations found in the entry

#### performance

Includes all entries belonging to a type listed in the
[collection_performance](http://base.uni-ak.ac.at/portfolio/taxonomy/collection_performance)
concept.

* `title` contains:
    - title
* `subtext` contains:
    - subtitle
* `primary_details` contains:
    - artists
    - date, time, location, location description
    - keywords
    - url
* `secondary_details` contains:
    - texts with types
    - material
    - format
* `list` contains:
    - contributors
* `location` contains:
    - all locations found in the entry

#### research project

Includes all entries belonging to a type listed in the
[collection_research_project](http://base.uni-ak.ac.at/portfolio/taxonomy/collection_research_project)
concept.

* `title` contains:
    - title
* `subtext` contains:
    - subtitle
* `primary_details` contains:
    - project lead
    - project partners
    - date range
    - keywords
    - url
* `secondary_details` contains:
    - texts with types
    - funding
    - funding category
    - status
* `list` contains:
    - contributors
* `location` should not be displayed for this type of activity

#### sculpture

Includes all entries belonging to a type listed in the
[collection_sculpture](http://base.uni-ak.ac.at/portfolio/taxonomy/collection_sculpture)
concept.

* `title` contains:
    - title
* `subtext` contains:
    - subtitle
* `primary_details` contains:
    - artists
    - date, location, location description
    - keywords
    - url
* `secondary_details` contains:
    - texts with types
    - material, format
    - dimensions
* `list` contains:
    - contributors
* `location` contains:
    - all locations found in the entry

#### software

Includes all entries belonging to a type listed in the
[collection_software](http://base.uni-ak.ac.at/portfolio/taxonomy/collection_software)
concept.

* `title` contains:
    - title
* `subtext` contains:
    - subtitle
* `primary_details` contains:
    - software developers
    - date
    - open source license
    - keywords
    - url
* `secondary_details` contains:
    - texts with types
    - programming language
    - git url
    - documentation url
    - software version
* `list` contains:
    - contributors
* `location` should not be displayed for this type of activity

#### Details on how to transform data

> TODO: add example screenshot, notes on base-components, note on combining multiple dates etc.




### Data flow

The following BPMN diagram shows the process (and data) flows, happening between
the different components of the Portfolio/Showroom ecosystem. The aim here is not to
describe any flows within a component, but give an overview of which actions in which
components trigger which API calls and worker jobs, based on data that has to be
(re-)rendered or in other ways processed.

Note that user interaction with Showroom Backend itself (through the Showroom Frontend),
is not listed here. This is because all direct user interactions with Showroom should
be able to be handled without interaction with other systems.

![Data Flow in the Showroom Ecosystem](data_flow.svg)
(full-size image: [](data_flow.svg)
bpmn source: [](data_flow.bpmn))
