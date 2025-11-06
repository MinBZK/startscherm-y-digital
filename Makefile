
.PHONY: run run-all stop postgres elastic nextcloud tika keycloak postgres-stop postgres-remove elastic-stop elastic-remove nextcloud-stop nextcloud-remove tika-stop tika-remove keycloak-stop keycloak-remove remove deploy deploy-dev deploy-prod build setup-cluster stop-cluster

run: postgres elastic tika nextcloud

run-all:
	docker compose up -d

postgres-stop:
	docker compose -f development/postgres/docker-compose.yml down

postgres-remove:
	docker compose -f development/postgres/docker-compose.yml down -v

elastic-stop:
	docker compose -f development/elasticsearch/docker-compose.yml down

elastic-remove:
	docker compose -f development/elasticsearch/docker-compose.yml down -v

nextcloud-stop:
	docker compose -f development/nextcloud/docker-compose.yml down

nextcloud-remove:
	docker compose -f development/nextcloud/docker-compose.yml down -v

tika-stop:
	docker compose -f development/tika/docker-compose.yml down

tika-remove:
	docker compose -f development/tika/docker-compose.yml down -v

stop: postgres-stop elastic-stop tika-stop nextcloud-stop

keycloak:
	docker compose -f development/keycloak/docker-compose.yml up -d

keycloak-stop:
	docker compose -f development/keycloak/docker-compose.yml down

keycloak-remove:
	docker compose -f development/keycloak/docker-compose.yml down -v

stop-all: stop

remove: postgres-remove elastic-remove tika-remove nextcloud-remove

postgres:
	docker compose -f development/postgres/docker-compose.yml up -d

elastic:
	docker compose -f development/elasticsearch/docker-compose.yml up -d

tika:
	docker compose -f development/tika/docker-compose.yml up -d

nextcloud:
	docker compose -f development/nextcloud/docker-compose.yml up -d

ingest-full:
	python3 backend/nextcloud_ingestor/src/main.py full

ingest-incremental:
	python3 backend/nextcloud_ingestor/src/main.py incremental

# Testing
test-install:
	pip install -r requirements-test.txt

test:
	python -m pytest test/ -v

test-activity:
	python -m pytest test/test_activity_api.py -v

test-all: test-install test

dockerhub-auth:
	cd deploy/helm && ./setup-dockerhub-auth.sh && cd ../..
# 	echo $(DOCKERHUB_PASSWORD) | docker login -u $(DOCKERHUB_USERNAME) --password-stdin

################################################################################

SHELL=/bin/bash

install-nginx:
	kubectl apply -f https://kind.sigs.k8s.io/examples/ingress/deploy-ingress-nginx.yaml --kubeconfig=deploy/skaffold/.kind-kubeconfig

restart-cluster: stop-cluster setup-cluster dockerhub-auth develop

setup-cluster:
	@[[ -n "$(shell kind get clusters | grep bsw)" ]] || kind create cluster --name bsw --kubeconfig deploy/skaffold/.kind-kubeconfig --config=deploy/skaffold/kind-config.yaml

stop-cluster:
	kind delete cluster --name bsw --kubeconfig ../skaffold/.kind-kubeconfig

k9s:
	k9s --kubeconfig deploy/skaffold/.kind-kubeconfig

update-kubeconfig:
	kind get kubeconfig --name bsw > deploy/skaffold/.kind-kubeconfig

develop: login-acr setup-cluster set-secret-values
	skaffold dev --profile dev --filename deploy/skaffold/skaffold.yaml --trigger=manual --status-check=false --kubeconfig=deploy/skaffold/.kind-kubeconfig

set-secret-values:
	cd deploy/skaffold && bash set-secret-values.sh

login-acr:
	az acr login --name ydigital

helm-dependency-update:
	helm dependency update deploy/helm/

test-templates:
	helm template test deploy/helm/ --dry-run --debug

psql:
	psql -p 5432 -h localhost -U user -d postgres

ingest-all: ingest-es ingest-case-law ingest-werk-instructie ingest-graphs

ingest-es:
	curl localhost:5000/system/create-es-indices && curl localhost:5000/system/ingest-es-from-blob-storage

ingest-case-law:
	curl localhost:5000/system/ingest-case-law-from-blob-storage

ingest-werk-instructie:
	curl localhost:5000/system/ingest-werk-instructie-from-blob-storage

ingest-graphs: ingest-jas ingest-taxonomy ingest-lido

ingest-jas:
	curl -XPOST -H "Content-Type: application/json" -d '{"blob_name": "JAS.ttl"}' localhost:5000/system/upload-graph

ingest-taxonomy:
	curl -XPOST -H "Content-Type: application/json" -d '{"blob_name": "Taxonomy.ttl"}' localhost:5000/system/upload-graph

ingest-lido:
	curl -XPOST -H "Content-Type: application/json" -d '{"blob_name": "lido.ttl"}' localhost:5000/system/upload-graph

ingest-selectielijsten:
	curl -XPOST -H "Content-Type: application/json" -d '{"file_name": "selectielijsten.csv"}' localhost:5000/system/upload-csv

test-pipeline: pipeline-test_1

pipeline-test_1:
	mkdir -p pipeline_data_outputs && curl -XPOST -H "Content-Type: application/json" -d '{"session_id": "1", "message": "Wanneer verwerkt de verwerkingsverantwoordelijke persoonsgegevens die niet reeds aan een geheimhoudingsplicht zijn onderworpen?"}' localhost:5000/pipeline > ./pipeline_data_outputs/output.txt && cat ./pipeline_data_outputs/output.txt | jq . > ./pipeline_data_outputs/output_1.json

reingest-users:
	curl -X POST "http://localhost:9200/global-user-info/_delete_by_query" -H 'Content-Type: application/json' -d'{"query": {"match_all": {}}}'
	curl "http://localhost:8080/run?mode=update&operation=users"

run-mail:
	curl "http://localhost:8080/run?mode=update&operation=mail"

run-content:
	curl "http://localhost:8080/run?mode=update&operation=content"

run-delta:
	curl "http://localhost:8080/run?mode=update&operation=delta"

run-users:
	curl "http://localhost:8080/run?mode=update&operation=users"

run-teams:
	curl "http://localhost:8080/run?mode=update&operation=teams"

create-indices:
	curl -X PUT "http://localhost:9200/global-user-info"
	curl -X PUT "http://localhost:9200/bsw-index" 
	curl -X PUT "http://localhost:9200/dossier-index"
	curl -X PUT "http://localhost:9200/deltas"
	curl -X PUT "http://localhost:9200/task-index"

delete-doc-indices:
	curl -X POST "http://localhost:9200/dossier-index/_delete_by_query" -H 'Content-Type: application/json' -d'{"query": {"match_all": {}}}'
	curl -X POST "http://localhost:9200/bsw-index/_delete_by_query" -H 'Content-Type: application/json' -d'{"query": {"match_all": {}}}'
	curl -X POST "http://localhost:9200/deltas/_delete_by_query" -H 'Content-Type: application/json' -d'{"query": {"match_all": {}}}'

startup-elastic: create-indices run-users run-delta run-content run-mail run-teams

delete-wir-indices:
	curl -X DELETE "http://localhost:9200/chunks" -H 'Content-Type: application/json'
	curl -X DELETE "http://localhost:9200/legal-documents" -H 'Content-Type: application/json'
	curl -X DELETE "http://localhost:9200/case-law-chunks" -H 'Content-Type: application/json'
	curl -X DELETE "http://localhost:9200/case-laws" -H 'Content-Type: application/json'
	curl -X DELETE "http://localhost:9200/werk-instructie-chunks" -H 'Content-Type: application/json'
	curl -X DELETE "http://localhost:9200/werk-instructie" -H 'Content-Type: application/json'

rerun-annotation:
	make delete-doc-indices && make startup-elastic

migrate:
	cd shared && alembic upgrade head
make-migrations:
	cd shared && alembic revision --autogenerate
