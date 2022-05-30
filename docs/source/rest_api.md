# REST API

_Showroom Backend_ provides an OpenAPI 3.0 compatible REST API, which is used by the
_Showroom Frontend_ to display all activities and entities published to _Showroom_,
as well as to allow authenticated users to adapt their description, showcase and
activity list display/ordering. Additionally, repositories authenticated through an
API key can push activities and entities to _Showroom_.

The OpenAPI 3.0 schema for _Showroom Backend_ is generated with
[drf-spectacular](https://drf-spectacular.readthedocs.io), which also provides a
_Swagger UI_ to interact with the API.

Once running, the API itself is available on the `/api/v1/` path, while the schema is
consumable under any of the following three paths:

* `/api/v1/schema/openapi3.json` - Open API 3.0 schema in JSON
* `/api/v1/schema/openapi3.yaml` - Open API 3.0 schema in YAML
* `/api/v1/schema/swagger-ui` - The Swagger UI to the schema described in the above two 

As an example reference you can also take a look at the Swagger UI of the current stable
release deployment of the University of Applied Arts Vienna:
[https://base.uni-ak.ac.at/showroom/api/v1/schema/swagger-ui](https://base.uni-ak.ac.at/showroom/api/v1/schema/swagger-ui)

