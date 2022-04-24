.PHONY: start-default
start-default:  ## start containers
	docker-compose pull --ignore-pull-failures
	docker-compose build --no-cache --pull ${PROJECT_NAME}-django
	docker-compose up -d --build

.PHONY: stop-default
stop-default:  ## stop containers
	docker-compose down

.PHONY: restart-default
restart-default:  ## restart containers
	docker-compose restart

.PHONY: git-update-default
git-update-default:  ## git pull as base user
	if [ "$(shell whoami)" != "base" ]; then sudo -u base git pull; else git pull; fi

.PHONY: init-default
init-default:  ## init django project
	docker-compose exec ${PROJECT_NAME}-django bash -c "pip-sync && python manage.py migrate && python manage.py collectstatic --noinput"

.PHONY: restart-gunicorn-default
restart-gunicorn-default:  ## gracefully restart gunicorn
	docker-compose exec ${PROJECT_NAME}-django bash -c 'kill -HUP `cat /var/run/django.pid`'

.PHONY: build-docs-default
build-docs-default:  ## build documentation
	docker build -t ${PROJECT_NAME}-docs ./docker/docs
	docker run --rm -it -v `pwd`/docs:/docs -v `pwd`/src:/src ${PROJECT_NAME}-docs bash -c "make clean html"

.PHONY: update-default
update-default: git-update init restart-gunicorn build-docs  ## update project (runs git-update init restart-gunicorn build-docs)

.PHONY: start-dev-docker-default
start-dev-docker-default: start-default  ## start docker development setup
	docker logs -f ${PROJECT_NAME}-django

.PHONY: pip-compile-default
pip-compile-default:  ## run pip-compile locally
	pip-compile src/requirements.in
	pip-compile src/requirements-dev.in

.PHONY: pip-compile-upgrade-default
pip-compile-upgrade-default:  ## run pip-compile locally with upgrade parameter
	pip-compile src/requirements.in --upgrade
	pip-compile src/requirements-dev.in --upgrade

.PHONY: pip-compile-docker-default
pip-compile-docker-default:  ## run pip-compile in docker container
	docker-compose exec ${PROJECT_NAME}-django pip-compile requirements.in
	docker-compose exec ${PROJECT_NAME}-django pip-compile requirements-dev.in

.PHONY: pip-compile-upgrade-docker-default
pip-compile-upgrade-docker-default:  ## run pip-compile in docker container with upgrade parameter
	docker-compose exec ${PROJECT_NAME}-django pip-compile requirements.in --upgrade
	docker-compose exec ${PROJECT_NAME}-django pip-compile requirements-dev.in --upgrade

.PHONY: init-pre-commit-default
init-pre-commit-default:  ## initialize pre-commit
	python3 -m pip install --upgrade pre-commit
	pre-commit install --install-hooks --overwrite

.PHONY: update-pre-commit-default
update-pre-commit-default: init-pre-commit-default  ## update pre-commit and hooks

.PHONY: update-config-default
update-config-default:  ## update config subtree
	git subtree pull --prefix config git@github.com:base-angewandte/config.git main --squash

.PHONY: help
help:  ## show this help message
	@echo 'usage: make [command] ...'
	@echo
	@echo 'commands:'
	@egrep -h '^(.+)\:.+##\ (.+)' ${MAKEFILE_LIST} | sed 's/-default//g' | sed 's/:.*##/#/g' | sort -t# -u -k1,1 | column -t -c 2 -s '#'

# https://stackoverflow.com/a/49804748
%: %-default
	@true
