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

## License

See `LICENSE`.

---
