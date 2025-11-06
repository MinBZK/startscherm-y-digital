CONTAINER:= nextcloud_ingestor
PROJECT:= ally
ifeq ($(origin VERSION),undefined)
VERSION:= develop
endif
ifeq ($(origin NAMESPACE),undefined)
NAMESPACE:= dev
endif
LOCAL_REPO:= localhost:32000
REMOTE_REPO:= ydigital.azurecr.io
IMAGE:=$(PROJECT)/$(NAMESPACE)/$(CONTAINER):$(VERSION)

build:
	DOCKER_BUILDKIT=1 docker build --network host  -t ${IMAGE} .

run:
	docker run --env-file .env --network host ${IMAGE}