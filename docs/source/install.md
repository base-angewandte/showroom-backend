# Installation guide

## Compatibility matrix

To use Showroom backend with all features, make sure to have the proper versions of
Portfolio and CAS running.

| Showroom Backend | Showroom Frontend | Portfolio Backend | CAS Backend |
| ---------------- | ----------------- | ----------------- | ----------- |
| 1.0.0            | 1.0.0             | 1.2.1             | 1.2.0       |

## Development

There are two supported ways to start the development server:

1. Start only the auxiliary servers (database and redis) in docker
   but start the django dev server locally in your virtual env. This
   is the preferred way if you actively develop this application.

2. Start everything inside docker containers. This is the "easy" way
   to start a dev server and fiddle around with it, hot reloading included.
   But you will not have the local pre-commit setup.

In both cases there are some common steps to follow:

- Install docker and docker-compose for your system. Make sure to not only have the
  `docker compose` plugin but the actual `docker-compose` binary installed.

- Clone git repository and checkout branch `develop`:

  ```bash
  git clone https://github.com/base-angewandte/showroom-backend.git
  cd showroom-backend
  ```

- Check and adapt settings:

  ```bash
  # env
  cp env-skel .env
  vi .env

  # django env
  cp ./src/showroom/env-skel ./src/showroom/.env
  vi ./src/showroom/.env
  ```

Take a look at the [](./configuration.md) section, for more details, if you need more
context than the comments in the skeleton env files give you.

Now, depending on which path you want to go, take one of the following two
subsections.

### Everything inside docker

- Make sure that the `DOCKER` variable in `./src/showroom/.env` is set to
  `TRUE`. Otherwise django will assume the postgres and redis are accessible
  on localhost ports.

- Now create the docker-compose override file:

  ```bash
  cp docker-compose.override.dev-docker.yml docker-compose.override.yml
  ```

- Start everything:

  ```bash
  make start-dev-docker
  ```

  Alternatively, if make is not installed on your system yet, you can
  also just use `docker-compose` directly:

  ```bash
  docker-compose up -d --build showroom-redis showroom-postgres showroom-django
  ```

  If you did start the service with the `docker-compose` instead of `make`, you
  might want to do the following to also get Django's debug output:

  ```bash
  docker logs -f showroom-django-dev
  ```

  To stop all services again, use `make stop` or `docker-compose down`.

### The full developer setup

> Disclaimer: make sure to explicitly set the relevant `POSTGRES_*` variables in your
> src/showroom/.env file, if you have changed any of the corresponding `SHOWROOM_DB_*`
> parameters in your .env file. This is not necessary for dockerised setups, but in your
> for local django dev server we those environement variables are not assigned
> automagically. Take a look at the [](./configuration.md) section for details.

- Create docker-compose override file:

  ```bash
  cp docker-compose.override.dev.yml docker-compose.override.yml
  ```

- Install latest python 3.8 and create virtualenv e.g. via `pyenv` and `pyenv-virtualenv`

- Install pip-tools and requirements in your virtualenv:

  ```bash
  pip install pip-tools
  cd src
  pip-sync requirements-dev.txt
  cd ..
  ```

- Install pre-commit hooks:

  ```bash
  pre-commit install
  ```

- Start required services:

  ```bash
  make start-dev
  ```

- Run migration:

  ```bash
  cd src
  python manage.py migrate
  ```

- Start development server:

  ```bash
  python manage.py runserver 8500
  ```

## Production

- Update package index:

  ```bash
  # RHEL
  sudo yum update

  # Debian
  sudo apt-get update
  ```

- Install docker and docker-compose

- Change to user `base`

- Change to `/opt/base`

- Clone git repository:

  ```bash
  git clone https://github.com/base-angewandte/showroom-backend.git
  cd showroom-backend
  ```

- Check and adapt settings:

  ```bash
  # env
  cp env-skel .env
  vi .env

  # django env
  cp ./src/showroom/env-skel ./src/showroom/.env
  vi ./src/showroom/.env
  ```

  If you want to use the user repository as well, you need an API key from your
  CAS / User Preferences instance. If you have not set this up yet, now is a good time
  to do so. Make sure to update the _src/showroom/.env_ file for the new API key then,
  and that DISABLE_USER_REPO is set to false (which is the default, if you did not
  remove the comment in the corresponding line).

- Use `Makefile` to initialize and run project:

  ```bash
  make start init restart-gunicorn
  ```

- Install nginx and configure it accordingly (clone the `nginx` repo to `/opt/base/nginx` and follow the setup docs there)

- Adopt the CAS service to allow authentication for Showroom

  - On the server where CAS is deployed, in /opt/base/cas/src/localsettings.py
    add the showroom service in the `MAMA_CAS_SERVICES` list. Take the portfolio
    service as a reference.
  - Afterwards go to /opt/base/cas and do a quick rebuild of the CAS container:
    ```bash
    sudo docker-compose stop cas-django && sudo docker-compose up --build -d cas-django
    ```

- Set up a source repository and the default institution:

  - Create a SourceRepository with an API key by using the management command:

    ```bash
    sudo docker-compose exec showroom-django python manage.py create_source_repository -h
    ```

    This gives you some context info on what we can feed this command with. We need at
    least a repo id (which is a self-chose integer), a URL where to reach the repo
    and an API key (which should be some generated password with a good strength, e.g.
    what you get from `pwgen -s 32 1`). Important for the repo url: this has to be the
    base URL to which the media paths are added. In the Angewandte's base setup this
    is https://base.uni-ak.ac.at instead of https://base.uni-ak.ac.at/portfolio (which
    one might think more accurate of the place where the actual repository lives).
    Additionally, it also would be nice to provide labels for the institution and the
    repository by using the `-l` and `-p` options, as well a URL to the institutions'
    website itself with the `-u` option. Those things can still be later changed through
    the Django admin interface. They are used for pre-rendering content, as soon
    as activities or entities are pushed from one of the repositories. Therefore, it is
    a good idea to make sure this is all set up beforehand.

    So the following would be a full-fledged command to set up a SourceRepository:

    ```bash
    sudo docker-compose exec showroom-django python manage.py create_source_repository -u "https://www.dieangewandte.at" -p "Portfolio" 1 GOy4Dq1f0Yftxr3r3G8Twr11K172Krzn "Universität für Angewandte Kunst Wien" "https://base.uni-ak.ac.at"
    ```

    Now we can use the new repo id to also create a first institution entity:

    ```bash
    sudo docker-compose exec showroom-django python manage.py create_institution 1 "Universität für Angewandte Kunst Wien"
    ```

    The repository ID now has to be set in the _src/showroom/.env_ file as the
    `DEFAULT_USER_REPO` setting. Also use the returned entity ID to set the
    `DEFAULT_ENTITY`. If you want several users to be able to edit this entity's
    showcase, then also set the `SHOWCASE_DEMO_ENTITY_EDITING` to this ID. Additionally,
    you have to also set the `SHOWCASE_DEMO_USERS` to a list of showcase entity IDs,
    which are allowed not only to edit their own page but also this one. This should
    be done as soon as you have your users synced from the repository.

    Afterwards do a `sudo make reload` to let the new settings become effective

- Adopt your repositories to use the new source repository API key:
  - in CAS / User Preferences you should set the `SHOWROOM_API_KEY` and the
    `SHOWROOM_BASE_URL` accordingly. Also set `SYNC_TO_SHOWROOM` to `True`.
  - in Portfolio there are:
    - `SYNC_TO_SHOWROOM` which should be `True`
    - `SHOWROOM_API_BASE` point to showrooms API root (e.g. https://base.uni-ak.ac.at/showroom/api/v1/ )
    - `SHOWROOM_API_KEY` with the key from above
    - `SHOWROOM_REPO_ID` with the repo ID from above

### Notes and disclaimers on prod deployments 🚧🤔🤬💡

Here are some notes on the deployment process, involving the nginx setup, but specific to the setup of Showroom.
These might help you debug and not stumble across the same obstacles over and over again:

- If this service is new and not yet configured, you will need to add at least the following files in the nginx repo:
  `showroom.conf`, `showroom-local.conf`, and `showroom-upstream.conf` as well as their testing counterparts (with a
  `-dev`-suffix to `showroom`). Use the existing files for portfolio files as a reference.
  - If you copy and modify the portfolio files, make sure to remove the `merge_slashes off` directive, otherwise nginx
    will throw an error, because the directive already gets included in the portfolio proxy configuration
- The `templates/nginx.conf.template` file has to be adopted for the new upstreams and includes.
- According environment variable lines have to be added to `docker-compose.yaml` and `docker-compose.override.yaml`.
  - Make sure to also add a network to the override template in `docker-compose.override.base.yaml` and your actual
    override file.
- For the nginx repo on the showroom node you will only need the showroom-specific environment variables and docker
  compose override directives:
  - for the .env file only the following four have to be set:
    `BASE_HOSTNAME`, `LETSENCRYPT_EMAIL`, `LETSENCRYPT_STAGING`, `SHOWROOM_STATIC`
  - the docker-compose.override.yaml should look like this (in this example for a testing server):
    ```yaml
    version: "3"
    services:
      nginx:
        environment:
          - SHOWROOM_DEV_LOCAL=
        volumes:
          - $SHOWROOM_STATIC:/showroom-static
        networks:
          showroom-backend_showroomnet:
            aliases:
              - $BASE_HOSTNAME
    networks:
      showroom-backend_showroomnet:
        external: true
    ```
- When everything is running you still have to make sure to generate the static files for showroom by doing
  `sudo docker exec showroom-django python manage.py collectstatic` on your deploy node.
  In some cases there might be an issue, e.g. when you completely redeploy showroom and
  delete its folders, while nginx is still up. Then the collectstatic will not work.
  In that case stop nginx first and and do the collectstatic before you start it again.
- When you restart the Showroom services after the nginx services are already up, and afterwards the proxy does not
  work anymore, try restarting the nginx services as well. Because it might happen sometimes that the showroom-django
  service receives a new IP, but the nginx service still uses the old IP for the showroom-django upstream.
