# bsw-api

Backend API for the Beter Samenwerken (BSW) platform. Provides:
* Authenticated data access (documents, dossiers, tasks, calendar)
* Search endpoints (keyword + chat pipeline + RAG)
* Graph + Elasticsearch + Azure Blob ingestion utilities
* Health and maintenance endpoints

The service is a Python FastAPI application served by Gunicorn/Uvicorn.

## Overview
The API aggregates and exposes knowledge, user-centric dashboard data (documents, tasks, calendar events, messages, news), and intelligent search/chat capabilities (pipeline, LLM-only, RAG) backed by Elasticsearch, a Fuseki RDF triple store (graph queries), and a PostgreSQL database.

## Architecture
FastAPI application (`src/main.py`):
* Routers under `src/api/routes/*` mounted into the main app.
* Service layer under `src/services/*` encapsulates business logic.
* IR (Information Retrieval) modules under `src/ir/*` for search, RAG, graph, database, ingestion.
* Generation layer (`src/generation/*`) for prompt templates and LLM answer interface.
* Authentication via Keycloak token verification (`src/dependencies/auth.py`) using `HTTPBearer` and JWT validation with public keys fetched from Keycloak.
* Elasticsearch ingest + chunking and embedding in `src/ir/search/ingest.py` and `src/dependencies/elastic/ingest.py`.
* Blob storage ingestion (documents, case law, werk instructies, knowledge graphs) via Azure SDK.
* Database access with SQLAlchemy models (`src/ir/db/models/`) and sessions defined in `src/ir/db/database.py`.

Request flow (example /api/search): Client -> FastAPI route -> Auth dependency validates token -> Service logic -> IR search pipeline -> Response JSON.

## Tech Stack
Runtime: Python 3.12
Framework: FastAPI served with Gunicorn (uvicorn workers)
Key Libraries:
* fastapi, uvicorn, gunicorn
* httpx (async HTTP client)
* SQLAlchemy + Alembic (RDBMS + migrations)
* elasticsearch-dsl (async) for ES indices
* azure-storage-blob for blob ingestion
* Jinja2 for prompt templating
* nltk, stopwordsiso, pandas for text/data processing
* langchain-openai, langchain-mistralai, transformers for LLM & embeddings
* python-jose[cryptography] for JWT validation


## Environment Variables
Collected from code (`os.getenv` usage):
```
DEBUG_REQUESTS=false            # Enable detailed request logging if 'true'
LOG_LEVEL=INFO                  # Uvicorn/Gunicorn log level
ACCESS_LOG=false                # Enable uvicorn access logs if 'true'

# Keycloak Auth
KEYCLOAK_SERVER_URL=http://localhost:8080
KEYCLOAK_INTERNAL_URL=          # Optional alternate internal URL
KEYCLOAK_URL=                   # Optional alternate URL
KEYCLOAK_REALM=realm
KEYCLOAK_CLIENT_ID=client-id
KEYCLOAK_CLIENT_SECRET=
KEYCLOAK_ISSUER=                # Overrides constructed issuer

# Search / Retrieval
ES_HOSTNAME=http://bsw-elasticsearch:9200
GRAPHDB_URL=http://localhost:3030

# Azure Blob Storage
AZURE_STORAGE_CONNECTION_STRING=your-connection-string
# (Knowledge graph container names are currently hardcoded: 'knowledge-graphs', 'bsw-selectielijsten')

```


## Development
Run locally (without container):
```bash
python src/main.py
```
Or via Uvicorn (hot reload for development):
```bash
uvicorn main:app --host 0.0.0.0 --port 5000 --reload
```

## API Endpoints
Base docs: `/api/docs`, OpenAPI JSON: `/api/openapi.json`, ReDoc: `/api/redoc`

Public (no auth dependency in code):
* `POST /chat`                    – Run full search/chat pipeline
* `POST /chat-llm`                – LLM-only chat
* `POST /api/pipeline`            – Returns pipeline raw data structure
* `GET  /api/create_dossier`      – Create dossier (service side-effect)

Authenticated (depend on `get_current_user_id`):
Documents:
* `GET /api/documents/latest`

Dossiers:
* `POST /api/dossiers/create`
* `GET  /api/dossiers/dossier/{dossier_id}`
* `PATCH /api/dossiers/dossier/{dossier_id}/opened`
* `GET  /api/dossiers/get_latest`
* `GET  /api/dossiers/get_all`

Calendar:
* `GET /api/calendar/get_week_events`

Tasks:
* `GET /api/tasks/get_tasks`

Search:
* `POST /api/search`              – Keyword + filter search

Start Screen:
* `GET /`                         – Start screen data (documents, tasks, calendar, news, messages)
* `GET /my_day` (placeholder returns None)
* `GET /my_dossiers` (placeholder)
* `GET /my_tasks` (placeholder)
* `GET /my_agenda` (placeholder)
* `GET /notifications` (placeholder)

System / Maintenance:
* `GET  /system/health`
* `GET  /system/create-es-indices`
* `GET  /system/ingest-es-from-blob-storage`
* `GET  /system/ingest-case-law-from-blob-storage`
* `GET  /system/ingest-werk-instructie-from-blob-storage`
* `POST /system/upload-graph`
* `GET  /system/graph-query-lawuri` (expects query params matching `GraphLawQuery`)
* `GET  /system/query-taxonomy`    (expects `GraphTaxonomyQuery`)
* `POST /system/upload-csv`
* `POST /system/chat-rag`          – RAG chat answer
* `POST /system/chat-llm`          – LLM chat (system variant)

## Authentication
Bearer token authentication using Keycloak JWT validation:
* Extracts token via `HTTPBearer` security scheme.
* Fetches realm public keys from `KEYCLOAK_SERVER_URL/realms/{realm}/protocol/openid-connect/certs` (hourly cache).
* Validates signature, issuer, and audience/azp against `KEYCLOAK_CLIENT_ID`.
* Provides user info (sub, preferred_username, name, etc.) to routes via dependency injection.
