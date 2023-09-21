include .env
export

PROJECT_NAME ?= showroom

include config/base.mk

.PHONY: cleanup
cleanup:  ## clear sessions
	docker-compose exec ${PROJECT_NAME}-django bash -c "python manage.py clearsessions && python manage.py django_cas_ng_clean_sessions"

.PHONY: init-rq
init-rq:  ## init rq containers
	docker-compose exec ${PROJECT_NAME}-rq-worker-1 bash -c "pip-sync"
	docker-compose exec ${PROJECT_NAME}-rq-worker-2 bash -c "pip-sync"
	docker-compose exec ${PROJECT_NAME}-rq-scheduler bash -c "pip-sync"

.PHONY: restart-rq
restart-rq:  ## restart rq containers
	docker-compose restart ${PROJECT_NAME}-rq-worker-1 ${PROJECT_NAME}-rq-worker-2 ${PROJECT_NAME}-rq-scheduler

.PHONY: start-dev
start-dev:  ## start containers for local development
	docker-compose pull
	docker-compose up -d \
		${PROJECT_NAME}-redis \
		${PROJECT_NAME}-postgres
