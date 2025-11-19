# BSW Platform – Ingestion & Knowledge Services

This repository hosts the ingestion & knowledge layer for the Beter Samenwerken (BSW) platform:

* Nextcloud document & dossier ingestion with full and incremental (Activity API) updates
* Search / RAG & domain APIs (bsw-api)
* Annotation / enrichment component
* Frontend (Next.js)
* Shared database models & migrations
* Deployment assets (Helm, Skaffold, docker-compose) for local dev and Kubernetes

---

## Components

| Path | Purpose |
|------|---------|
| `backend/nextcloud_ingestor` | FastAPI + CLI for full & incremental ingestion from Nextcloud into Elasticsearch, state in Postgres. |
| `backend/bsw-api` | Main platform API: search (keyword, chat, RAG), dossier & document endpoints, auth via Keycloak. |
| `backend/annotation` | Placeholder / pipeline for enrichment & tagging of ingested documents. |
| `frontend/` | Next.js application (App Router) consuming API services. |
| `shared/` | Alembic migrations, shared scripts & upload utilities. |
| `deploy/helm` | Helm chart: Nextcloud, Postgres, Ingestor (API / jobs / schedulers), cron jobs. |
| `deploy/skaffold` | Local Kubernetes dev (Kind + Skaffold). |
| `development/` | Docker Compose stacks for isolated local services, for local development purposes (postgres, elasticsearch, nextcloud, tika, keycloak). |

---

## Local setup

* Generate TLS certificate and key files for HTTPS access. You could do so using `mkcert frontend.localhost`.
* Copy the .example.env file in deploy/skaffold and update the required values. Minimal requirements are `GPT_EMBEDDINGS_KEY` and `VLAM_API_KEY`. Add paths to the certificate and key files generated in the previous step under `FRONTEND_TLS_CERT` and `FRONTEND_TLS_KEY`.
* Run `make develop` from the main directory.
* Run `make install-nginx`.
* The Startscherm can be accessed via `https://frontend.localhost:8443`. Log in with keycloak. For local development, a default admin user is created using username *admin* and password corresponding to the value of auth.userPassword in deploy/helm/values.yaml.


---

## License

See `LICENSE`.

---
