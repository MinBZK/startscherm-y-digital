CONTAINER:= bsw-api
PROJECT:= bsw
ifeq ($(origin VERSION),undefined)
VERSION:= develop
endif
ifeq ($(origin NAMESPACE),undefined)
NAMESPACE:= dev
endif
LOCAL_REPO:= localhost:32000
REMOTE_REPO:= ydigital.azurecr.io
IMAGE:=$(PROJECT)/$(NAMESPACE)/$(CONTAINER):$(VERSION)

help:
	@echo ''
	@echo 'Usage: make [TARGET] [EXTRA_ARGUMENTS]'
	@echo 'Targets:'
	@echo '  build    	build docker --image-- '
	@echo '  run  		run docker --image-- '
build:
	cd .. && DOCKER_BUILDKIT=1 docker build --network=host --ssh default=$$SSH_AUTH_SOCK -f bsw-api/Dockerfile -t $(IMAGE) .
build-nc:
	cd .. && DOCKER_BUILDKIT=1 docker build --no-cache --network=host --ssh default=$$SSH_AUTH_SOCK -f bsw-api/Dockerfile -t $(IMAGE) .
run:
	docker run -p 5000:5000 $(IMAGE)
run-bash:
	docker run -it -p 5000:5000 --entrypoint=/bin/bash $(IMAGE)
push-local:
	docker tag $(IMAGE) ${LOCAL_REPO}/$(IMAGE)
	docker push ${LOCAL_REPO}/$(IMAGE)
push-remote:
	docker tag $(IMAGE) ${REMOTE_REPO}/$(IMAGE)
	docker push ${REMOTE_REPO}/$(IMAGE)
yeet: build push-remote


migrate:
	cd src && alembic upgrade head
make-migrations:
	cd src && alembic revision --autogenerate