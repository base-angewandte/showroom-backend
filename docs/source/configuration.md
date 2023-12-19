# Configuration

_Showroom Backend_ is configured through two `.env` files. For both there is a template
`env-skel` file available in the same folder, to copy from and then modify it. See
also [](install.md) on when and how to set up those files.

## `.env`

The first and shorter one is in the project root folder. It is used to configure the
docker services, for database credentials and the static assets folder. The defaults
are fine, only the `SHOWROOM_DB_PASSWORD` should be set to a strong password.

> Note: we wrote _should_, because programmatically nothing keeps you from using the
> default _password_. But in terms of nearly any security policy you absolutely _MUST_
> set a strong password here. Try e.g. `pwgen -s 32 1`.

## `/src/showroom/.env`

The main configuration environment file is in the _src/showroom_ folder, and it is
parsed in the Django settings initialization. All available settings are commented,
but some are more self-explanatory than others. Some only really make sense, once
you grasp the whole architectural ecosystem. So here you find some notes to shed more
light on those settings that might seem more opaque, or that are absolutely needed
to run.

### DOCKER

For any online deployment the default (True) should be fine here, as usually all
services will be run inside docker containers. Only when you want to start the
Django application itself on your host machine (e.g. for local development), you have
to set this to False.

### SITE_URL & FORCE_SCRIPT_NAME

The `SITE_URL` has to be set to the base URL of the site _Showroom_ is running on, which
will depend on whether you deploy this to some online node, either with multiple services
sharing one domain or running _Showroom_ on a separate domain, or if you run it locally.
For local development setups you can choose `http://127.0.0.1:8500/`. For an online
deployment choose the base path (protocol and domain), e.g. `https://base.uni-ak.ac.at/`.

Additionally, `FORCE_SCRIPT_NAME` (which defaults to `/showroom`) will be used to
determine the actual PATH to your _Showroom_ instance, by prefixing it with the
`SITE_URL`. So for a local development setup (where Django is actually running on
127.0.0.1:8500) make sure to remove the comment and explicitly set this to an empty
string:

```
FORCE_SCRIPT_NAME=
```

Do the same if your _Showroom_ runs on the root of a dedicated domain, and leave the
default if it runs on a shared domain where it runs on the _/showroom_ path.

### BEHIND_PROXY

This defines whether your application is running behind a reverse proxy (e.g. nginx).
In most cases the default True will be fine here. But for local development you might
want to set this to False.

### CAS\_\*

The `CAS_SERVER` points to the base path of your authentication server (e.g.
https://base.uni-ak.ac.at/cas/). `CAS_REDIRECT_URL` then points to the path on your
_Showroom_ to which the authentication server should redirect once the user's login
was successful.

### EMAIL\_\*

All settings in the block prefixed with `EMAIL_` are needed if you want to receive
e-Mail notifications from Django. While this is usually not necessary for local
development environments, it is highly advised for staging and production deployments,
especially if you don't have a Sentry instance running.

### CORS\_\* & CSRF\_\*

For the frontend to work and being able to make authenticated requests on behalf
of the user you should minimally set `CORS_ALLOW_CREDENTIALS` to True. All other
settings should basically be fine by default, as long as your frontend runs on the
same domain as the backend. If you need frontends on different domains (e.g. for
testing and staging purposes) to be able to make those request, you should add them
to the `CSRF_TRUSTED_ORIGINS` and `CORS_ALLOWED_ORIGINS` lists.

### POSTGRES\_\* & REDIS\_\*

For both databases the `*_PORT` setting should be fine by default, unless you explicitly
use a different port for those docker services.

The `POSTGRES_PASSWORD` has to be the same as the one set in the root folder _.env_ file.
If you deploy everything with docker, you don't have to set it here explicitly, as the
environment variable will already be set by docker based on the root _.env_ file.

### DISABLE_USER_REPO & USER\_\*

Your user repository will most likely be the same as the authentication server, the
CAS component with the User Preferences app. In order to be able to sync not only
activities but also the entities (specifically the persons publishing those activities),
you need to enable user repo by setting `DISABLE_USER_REPO` to False. This will be
the standard mode of operation in most scenarios.

But the default here is set to True, so you can get the _Showroom Backend_ running
in a first version, to later connect it to the user repo. Once you do this, you also
have to set the `USER_PREFERENCES_API_BASE` path and the `USER_PREFERENCES_API_KEY`,
which you have to create in the user repo.

### DEFAULT_USER_REPO

This relates to a _SourceRepository_ you have set up in Showroom. Most likely to the
one set with the management command during [](install.md). In almost all scenarios
this then relates to the same user repo that you are setting up with the values in
the last section. Functionally though, this is only used Showroom-internally to be able
to associate _ShowroomObjects_ of type entity (person, department, institution) with the
corresponding source repository from which the activities are pushed.

### CURRENTNESS_PAST_WEIGHT

This is the value that past events are multiplied with, when the `currentness` ordering
is applied to search results. See [Ranking and sorting](ranking_and_sorting)

### DEFAULT_ENTITY

This should most likely be set to the one institution created during [](install.md).

### SHOWCASE_DEMO\_\*

While in a future version of Showroom, the handling of organisational units will be
available through an administrative interface, for now we can only add organisational
entities manually through the Django admin. And while all users are allowed to edit
the showcase of their own (person) entity - the user page - there is no dynamic way
to allow different users to edit other entity pages.

Therefore, we can - for now - use the `SHOWCASE_DEMO_USERS` to set a list of Showroom
entity IDs, that are allowed to not only edit their own page, but also to edit a defined
set of other entity pages. This defined set of entity pages is configured with the
`SHOWCASE_DEMO_ENTITY_EDITING` list: a list of entity IDs that are allowed to be
edited by the `SHOWCASE_DEMO_USERS`.
