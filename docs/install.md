# Installation guide

## Development

There are two supported ways to start the development server:

1. Start only the auxiliary servers (database and redis) in docker
   but start the django dev server locally in your virtual env. This
   is the preferred way if you actively develop this application.

2. Start everything inside docker containers. This is the "easy" way
   to start a dev server and fiddle around with it, hot reloading included.
   But you will not have the local pre-commit setup.

In both cases there are some common steps to follow:

* Install docker and docker-compose for your system

* Clone git repository and checkout branch `develop`:

    ```bash
    git clone https://basedev.uni-ak.ac.at/redmine/showroom-backend.git
    cd showroom-backend
    ```

* Check and adapt settings:

    ```bash
    # env
    cp env-skel .env
    vi .env

    # django env
    cp ./src/showroom/env-skel ./src/showroom/.env
    vi ./src/showroom/.env
    ```

Now, depending on which path you want to go, take one of the following two
subsections.

### Everything inside docker

* Make sure that the `DOCKER` variable in `./src/showroom/.env` is set to
  `TRUE`. Otherwise django will assume the postgres and redis are accessible
  on localhost ports.

* Now create the docker-compose override file:

    ```bash
    cp docker-compose.override.dev-docker.yml docker-compose.override.yml
    ```

* Start everything:

    ```bash
    make start-dev-docker
    ```

  Alternatively, if make is not installed on your system yet, you can
  also just use `docker-compose` directly:

    ```bash
    docker-compose up --build showroom-redis showroom-postgres showroom-django
    ```

### The full developer setup

* Create docker-compose override file:

    ```bash
    cp docker-compose.override.dev.yml docker-compose.override.yml
    ```

* Install latest python 3.8 and create virtualenv e.g. via `pyenv` and `pyenv-virtualenv`

* Install pip-tools and requirements in your virtualenv:

    ```bash
    pip install pip-tools
    cd src
    pip-sync requirements-dev.txt
    cd ..
    ```

* Install pre-commit hooks:

    ```bash
    pre-commit install
    ```

* Start required services:

    ```bash
    make start-dev
    ```

* Run migration:

    ```bash
    cd src
    python manage.py migrate
    ```

* Start development server:

    ```bash
    python manage.py runserver 8500
    ```


## Production

* Update package index:

    ```bash
    # RHEL
    sudo yum update

    # Debian
    sudo apt-get update
    ```

* Install docker and docker-compose

* Change to user `base`

* Change to `/opt/base`

* Clone git repository:

    ```bash
    git clone https://base@basedev.uni-ak.ac.at/redmine/showroom-backend.git
    cd showroom-backend
    ```

* Check and adapt settings:

    ```bash
    # env
    cp env-skel .env
    vi .env

    # django env
    cp ./src/showroom/env-skel ./src/showroom/.env
    vi ./src/showroom/.env
    ```

* Use `Makefile` to initialize and run project:

    ```bash
    make start init init-static restart-gunicorn
    ```

* Install nginx and configure it accordingly
