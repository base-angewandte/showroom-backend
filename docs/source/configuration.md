# Configuration

*Showroom Backend* is configured through two `.env` files. For both there is a template
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

### SITE\_URL & FORCE\_SCRIPT\_NAME

The `SITE_URL` has to be set to the base URL of the site *Showroom* is running on, which
will depend on whether you deploy this to some online node, either with multiple services
sharing one domain or running *Showroom* on a separate domain, or if you run it locally.
For local development setups you can choose `http://127.0.0.1:8500/`. For an online
deployment choose the base path (protocol and domain), e.g. `https://base.uni-ak.ac.at/`.

Additionally, `FORCE_SCRIPT_NAME` (which defaults to `/showroom`) will be used to
determine the actual PATH to your *Showroom* instance, by prefixing it with the
`SITE_URL`. So for a local development setup (where Django is actually running on
127.0.0.1:8500) make sure to remove the comment and explicitly set this to an empty
string:
```dotenv
FORCE_SCRIPT_NAME=
```

Do the same if your *Showroom* runs on the root of a dedicated domain, and leave the
default if it runs on a shared domain where it runs on the _/showroom_ path.

### BEHIND\_PROXY

This defines whether your application is running behind a reverse proxy (e.g. nginx).
In most cases the default True will be fine here. But for local development you might
want to set this to False.

### CAS\_*

The `CAS_SERVER` points to the base path of your authentication server (e.g.
https://base.uni-ak.ac.at/cas/). `CAS_REDIRECT_URL` then points to the path on your
*Showroom* to which the authentication server should redirect once the user's login
was successful.
