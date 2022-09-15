# Changelog

## 1.0.0-pre-release

This is the first production version of Showroom backend. This is tagged as pre-release,
because the dependencies to Portfolio and CAS backends are due to be bumped after their
release process for the next minor version is completed.

For details see the documentation in `./docs`, which will also be built to
https://showroom-backend.readthedocs.io after the current release.

The core features of Showroom backend are provided by API endpoints to:

- retrieve activities and entities (persons, departments, institutions)
- update entity showcase and activity lists for authenticated users
- retrieve an initial/front page entity (e.g. the hosting institution)
- retrieve user information or authenticated users
- retrieve the original repository data for authenticated API clients
- search across all showroom objects, based on search filters
- autocomplete search terms
- post and delete activities, media and relations for authenticated repos (Portfolio)
- post full entity information for authenticated user repos (CAS)

Additionally, the following auxiliary features are noteworthy:

- configuration of all relevant settings through an environment file
- management commands to add repositories and institution entities
- publishing log with configurable retention period
- asynchronous jobs to pre-render information, update indices, and grab missing entity
  information from the user repository
