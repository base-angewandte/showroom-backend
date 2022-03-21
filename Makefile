include .env
export


start:
	docker-compose up -d --build

stop:
	docker-compose down

restart:
	docker-compose restart

git-update:
	if [ "$(shell whoami)" != "base" ]; then sudo -u base git pull; else git pull; fi

init:
	docker-compose exec showroom-django bash -c "pip-sync && python manage.py migrate"

init-static:
	docker-compose exec showroom-django bash -c "python manage.py collectstatic --noinput"

cleanup:
	docker-compose exec showroom-django bash -c "python manage.py clearsessions && python manage.py django_cas_ng_clean_sessions"

build-showroom:
	docker-compose build showroom-django

restart-gunicorn:
	docker-compose exec showroom-django bash -c 'kill -HUP `cat /var/run/django.pid`'

restart-rq:
	docker-compose restart showroom-rq-worker-1 showroom-rq-worker-2

reload: restart-gunicorn restart-rq

update: git-update init init-static restart-gunicorn

start-dev:
	docker-compose up -d --build \
		showroom-redis \
		showroom-postgres

start-dev-docker:
	docker-compose up -d --build \
		showroom-redis \
		showroom-postgres \
		showroom-django
	docker exec showroom-django-dev python manage.py migrate
	docker logs -f showroom-django-dev

pip-compile:
	pip-compile src/requirements.in
	pip-compile src/requirements-dev.in

pip-compile-upgrade:
	pip-compile src/requirements.in --upgrade
	pip-compile src/requirements-dev.in --upgrade
