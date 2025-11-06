# NextCloud Ingestor

FastAPI service and CLI for ingesting documents and dossier metadata from a Nextcloud instance into Elasticsearch, with incremental updates driven by the Nextcloud Activity API and state persisted in PostgreSQL. It also performs optional full‑text extraction (Tika, PyMuPDF, plain text) and maintains dossier statistics (file count & total size).

## Key Features

* Full ingestion: traverses all users and their dossier folders, (re)creates indices, (re)indexes everything.
* Incremental ingestion: uses the Activity API to only process changed, created, moved/renamed, or deleted files since the last run.
* Robust dossier detection and metadata enrichment (members/sharees, creation time, size stats, Nextcloud file_id).
* Multi‑strategy resolution of dossier folder `file_id` (WebDAV PROPFIND, metadata, Activity API fallback).
* Document model with paragraph extraction for supported file types (PDF, Office docs, text, markdown).
* Pluggable content extraction via Tika server, with graceful fallback.
* State tracking in PostgreSQL (`activity_state` table) to resume incremental ingestion accurately.
* Dry‑run mode to validate traversal and counts without writing to Elasticsearch.
* FastAPI endpoints to trigger full or incremental ingest asynchronously.


## Core Modules

* `config.py` – Loads environment variables into an immutable `Config` dataclass.
* `nextcloud.py` – Wraps WebDAV & OCS APIs: listing users, groups, shares; activity retrieval; ACL & sharee resolution; metadata extraction.
* `ingestor.py` – Orchestrates full & incremental ingestion, dossier discovery, changed file handling, document building, and statistics updates.
* `elastic.py` – Index management and bulk operations for documents & dossiers; incremental updates & deletions.
* `content.py` – Full‑text extraction through Tika (preferred) with fallbacks; supports defined extensions.
* `database.py` / `state_manager.py` – SQLAlchemy models & state tracking of the last processed activity for incremental ingest.
* `utils.py` – Logging setup, hashing helper, supported extensions constant.
* `main.py` – FastAPI app and CLI entry points (`api`, `full`, `incremental`).

## Data Flow (Full Ingestion)
1. Load config (.env).
2. Initialize indices if absent.
3. Enumerate Nextcloud users → for each user, locate dossier parent folder (e.g. `dossiers`).
4. For each dossier: gather tree stats (file count, cumulative size, earliest creation), sharees (users/groups), folder `file_id`.
5. For each file under a dossier: read bytes, gather metadata (size, modified/created time, mime/type, Nextcloud fileid), extract text & paragraphs if supported, build document schema.
6. Bulk index dossiers, then documents.
7. Persist latest activity ID to PostgreSQL for future incremental runs.

## Data Flow (Incremental Ingestion)
1. Read last activity ID from PostgreSQL.
2. Fetch activities > last_activity_id (ascending order).
3. Detect new dossiers, index them before file processing.
4. Categorize file activities: created, updated, deleted, moved/renamed.
5. Delete removed files; reindex changed/created files updating dossier stats (file count, size deltas).
6. Update last_activity_id to newest processed.

## Document Schema (selected fields)
```
{
	title, raw_title, nextcloud_id, url, author, accessible_to_users[],
	dossier_id, dossier_name, filepath, created_date, lastmodifiedtime,
	filetype, size, full_text, paragraphs[{id,text}], lastmodified_user_id
}
```

## Dossier Schema (selected fields)
```
{
	dossier_id, dossier_name, file_id, webURL, owner_userid,
	members[], created_datetime, lastmodified_datetime,
	file_count, total_size, unopened, description
}
```

## Supported File Types for Extraction
`.pdf, .docx, .doc, .ppt, .pptx, .xls, .xlsx, .txt, .md`

Extraction order: Tika server → specialized fallback (PyMuPDF for PDF) → raw text decode for `.txt` / `.md`.

## Environment Configuration

Create a `.env` (you can start from `.env.example`):

| Variable | Purpose | Required |
|----------|---------|----------|
| `NEXTCLOUD_URL` | Base URL of Nextcloud instance | yes |
| `NEXTCLOUD_ADMIN_USERNAME` | Auth username | yes |
| `NEXTCLOUD_ADMIN_PASSWORD` | Auth password | yes |
| `NEXTCLOUD_DOSSIER_PARENT_PATH` | Folder under each user containing dossiers (default `dossiers`) | no |
| `ELASTICSEARCH_URL` | Elasticsearch base URL | yes (for real runs) |
| `ELASTICSEARCH_INDEX_DOCUMENTS` | Documents index name | no |
| `ELASTICSEARCH_INDEX_DOSSIERS` | Dossiers index name | no |
| `POSTGRES_HOST` / `PORT` / `DB` / `USER` / `PASSWORD` | PostgreSQL connection | yes (incremental) |
| `TIKA_SERVER_URL` | Tika server endpoint | no |
| `DRY_RUN` | `true` to avoid writes to ES | no |
| `ES_URL`, `ES_INDEX_DOCUMENTS`, `ES_INDEX_DOSSIERS` | Alternate ES variable names used in `elastic.py` | no |
| `ES_USER`, `ES_PASSWORD` | Optional basic auth for ES | no |
| `NC_URL`, `NC_USER`, `NC_PASSWORD` | Alternate Nextcloud env names used in `nextcloud.py` | no |

Note: Code supports dual naming (e.g. `NC_URL` or `NEXTCLOUD_URL`). Prefer the `NEXTCLOUD_*` set for consistency.

## Running

### CLI Modes
```bash
python src/main.py api          # start FastAPI (dev reload)
python src/main.py full         # run full ingestion once
python src/main.py incremental  # run incremental ingestion once
```


## FastAPI Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Health/info message |
| POST | `/ingest/full` | Start asynchronous full ingestion (recreates indices if missing) |
| POST | `/ingest/incremental` | Start asynchronous incremental ingestion based on Activity API |
| GET | `/run` | Legacy: triggers full ingestion (kept for backwards compatibility) |

Request body is empty; you may optionally pass `?dry_run=true` query or JSON param to override env dry run.


## State Management
The table `activity_state` stores the last processed `last_activity_id` and timestamps. On first run it is auto‑initialized. Incremental ingestion uses this to request only newer activities and updates it after successful processing.

## Dry Run Mode
Set `DRY_RUN=true` (or pass `dry_run=true` parameter) to traverse Nextcloud, build documents/dossiers in memory, but skip writing to Elasticsearch. Useful for validating permissions, performance, and counts.

## Testing

This README documents the runtime (`backend/nextcloud_ingestor`) module only; test details are covered separately in `test/README.md`.

