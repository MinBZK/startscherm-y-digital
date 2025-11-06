import os
from elasticsearch import Elasticsearch, helpers, ApiError
from elasticsearch.helpers import BulkIndexError
from utils import logger, hash
from typing import Iterable
from urllib.parse import urlparse
import datetime

# ENV
ES_URL = os.getenv("ES_URL", "http://localhost:9200")
ES_INDEX_DOCUMENTS = os.getenv("ES_INDEX_DOCUMENTS", "bsw-index")
ES_INDEX_DOSSIERS = os.getenv("ES_INDEX_DOSSIERS", "dossier-index")
ES_USER = os.getenv("ES_USER", None)
ES_PASSWORD = os.getenv("ES_PASSWORD", None)


class ESClient:
    def __init__(self, dry_run: bool = False):
        if not dry_run:
            parsed = urlparse(ES_URL)
            if parsed.path not in ("", "/"):
                raise ValueError(f"ES_URL must not include a path: {ES_URL}")
            logger.info(f"Connecting to Elasticsearch at {ES_URL}")
            self.es = Elasticsearch(
                ES_URL,
                http_auth=(ES_USER, ES_PASSWORD) if ES_USER and ES_PASSWORD else None,
                headers={"Accept": "application/json"}
            )
        self.dry_run = dry_run
        self.index_docs = ES_INDEX_DOCUMENTS
        self.index_dossiers = ES_INDEX_DOSSIERS

        print(f"ESClient initialized with dry_run={self.dry_run}")
        print(f"ES_URL={ES_URL}, ES_INDEX_DOCUMENTS={ES_INDEX_DOCUMENTS}, ES_INDEX_DOSSIERS={ES_INDEX_DOSSIERS}")

    def create_indices(self):
        """ Check if indices exist, and create them if not. """
        if self.dry_run:
            logger.info("Dry run: skipping index creation")
            return
        
        for idx, mapping in [
            (ES_INDEX_DOCUMENTS, self._documents_mapping()),
            (ES_INDEX_DOSSIERS, self._dossiers_mapping()),
        ]:
            try:
                if self.es.indices.exists(index=idx):
                    logger.info("Index %s already exists", idx)
                    # index exists
                    continue
                logger.info("Creating index %s", idx)
                self.es.indices.create(index=idx, body=mapping)
                logger.info("Created index %s", idx)
            except ApiError as e:
                logger.error(f"Elasticsearch error on index {idx}: {e}")
                raise

    def _index_docs(self, docs: Iterable[dict], index: str):
        def generate_actions():
            for d in docs:
                # Ensure we have a valid document ID
                nextcloud_id = d.get("nextcloud_id")
                dossier_id = d.get("dossier_id", "")
                
                if nextcloud_id:
                    doc_id = hash(nextcloud_id)
                elif dossier_id:
                    doc_id = dossier_id
                else:
                    logger.warning(f"Document without nextcloud_id or dossier_id: {d}")
                    doc_id = hash(str(d))  # Fallback: hash the entire document
                
                yield {
                    "_index": index,
                    "_id": doc_id,
                    "_source": d
                }

        try:
            actions = list(generate_actions())
            logger.debug(f"Generated {len(actions)} actions for bulk indexing")
            helpers.bulk(self.es, actions)
            logger.info(f"Successfully indexed {len(actions)} documents to {index}")
        except helpers.BulkIndexError as e:
            logger.error(f"Bulk indexing failed. {len(e.errors)} document(s) failed to index.")
            
            # Log details about each failed document
            for i, error in enumerate(e.errors[:5]):  # Show first 5 errors
                logger.error(f"Error {i+1}: {error}")
                
                # Try to identify the problematic document
                if 'index' in error and 'error' in error['index']:
                    error_info = error['index']['error']
                    doc_id = error['index'].get('_id', 'unknown')
                    logger.error(f"Document ID {doc_id} failed: {error_info.get('type', 'unknown')} - {error_info.get('reason', 'no reason')}")
            
            if len(e.errors) > 5:
                logger.error(f"... and {len(e.errors) - 5} more errors")
            
            # Re-raise with more context
            raise Exception(f"Failed to index {len(e.errors)} document(s) to {index}. See logs above for details.") from e
    
    def do_index_documents(self, docs: Iterable[dict]):
        # Convert to list to allow inspection and counting
        docs_list = list(docs)
        logger.info(f"Preparing to index {len(docs_list)} documents")
        
        # Log sample document for debugging
        if docs_list:
            sample_doc = docs_list[0]
            logger.debug(f"Sample document keys: {list(sample_doc.keys())}")
            logger.debug(f"Sample document nextcloud_id: {sample_doc.get('nextcloud_id', 'NOT_SET')}")
            
        if self.dry_run:
            logger.info("Dry run: would index %d documents into %s", len(docs_list), ES_INDEX_DOCUMENTS)
            return
            
        self._index_docs(docs_list, ES_INDEX_DOCUMENTS)

    def _update_docs(self, docs: Iterable[dict], index: str):
        actions = ({
            "_op_type": "update",
            "_index": index,
            "_id": hash(d.get("nextcloud_id")) or d.get("dossier_id", ""),
            "doc": d,
            "doc_as_upsert": True,
        } for d in docs)
        helpers.bulk(self.es, actions)

    def update_documents(self, docs: Iterable[dict]):
        # check if document exist
        existing_docs = []
        for doc in docs:
            # Normalize timestamps
            doc['created_date'] = self._normalize_timestamp(doc.get("created_date"))
            doc['lastmodifiedtime'] = self._normalize_timestamp(doc.get("lastmodifiedtime"))

            id = doc.get("nextcloud_id")
            doc_exists = self.es.exists(index=ES_INDEX_DOCUMENTS, id=id)
            if doc_exists:
                existing_docs.append(doc)
        new_docs = [d for d in docs if d not in existing_docs]
        logger.debug(f"Updating {len(existing_docs)} existing documents, indexing {len(new_docs)} new documents")

        if not self.dry_run:
            self._index_docs(new_docs, ES_INDEX_DOCUMENTS)
            self._update_docs(existing_docs, ES_INDEX_DOCUMENTS)

    def update_dossiers(self, dossiers: Iterable[dict]):
        existing_dossiers = []
        for dossier in dossiers:
            # Normalize timestamps
            dossier['created_datetime'] = self._normalize_timestamp(dossier.get("created_datetime"))
            dossier['lastmodified_datetime'] = self._normalize_timestamp(dossier.get("lastmodified_datetime"))

            id = dossier.get("dossier_id")
            dossier_exists = self.es.exists(index=ES_INDEX_DOSSIERS, id=id)
            if dossier_exists:
                existing_dossiers.append(dossier)
        new_dossiers = [d for d in dossiers if d not in existing_dossiers]
        logger.debug(f"Updating {len(existing_dossiers)} existing dossiers, indexing {len(new_dossiers)} new dossiers")

        if not self.dry_run:
            self._index_docs(new_dossiers, ES_INDEX_DOSSIERS)
            self._update_docs(existing_dossiers, ES_INDEX_DOSSIERS)

    def _normalize_timestamp(self, ts: str) -> str | None:
        """Normalize various timestamp formats to ISO 8601 date string (YYYY-MM-DDTHH:MM:SSZ)."""
        if not ts:
            return None
        # Try parsing common formats
        for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S", "%a, %d %b %Y %H:%M:%S %Z"):
            try:
                dt = datetime.datetime.strptime(ts, fmt)
                return dt.isoformat() + "Z"
            except ValueError as e:
                continue
        logger.warning(f"Unrecognized timestamp format: {ts}")
        # Fallback: return as-is (Elasticsearch may still parse it)
        return ts

    def do_index_dossiers(self, dossiers: list[dict]):
        logger.debug(f"Indexing dossiers: {dossiers}")
        actions = ({
            "_index": ES_INDEX_DOSSIERS,
            "_source": {
                **d,
                "created_datetime": self._normalize_timestamp(d["created_datetime"]),
            }
        } for d in dossiers)
        if self.dry_run:
            count = sum(1 for _ in actions)
            logger.info("Dry run: would index %d dossiers into %s", count, ES_INDEX_DOSSIERS)
            return
            
        try:
            result = helpers.bulk(self.es, actions)
            logger.info(f"Successfully indexed {len(dossiers)} dossiers. Result: {result}")
        except Exception as e:
            logger.error(f"Failed to index dossiers: {e}")
            raise


    # Incremental update methods
    def delete_documents_by_path(self, file_paths: set[str]):
        """Delete documents from ES based on their file paths."""
        if not file_paths:
            return
            
        if self.dry_run:
            logger.info("Dry run: would delete %d documents with paths: %s", 
                       len(file_paths), list(file_paths)[:5])
            return
            
        # Create delete queries for each path
        for file_path in file_paths:
            try:
                query = {
                    "query": {
                        "term": {
                            "filepath.keyword": file_path
                        }
                    }
                }
                
                result = self.es.delete_by_query(
                    index=self.index_docs,
                    body=query,
                    refresh=True
                )
                
                deleted_count = result.get("deleted", 0)
                if deleted_count > 0:
                    logger.info(f"Deleted {deleted_count} documents for path: {file_path}")
                else:
                    logger.debug(f"No documents found to delete for path: {file_path}")
                    
            except Exception as e:
                logger.error(f"Failed to delete documents for path {file_path}: {e}")

    def update_dossier_stats(self, dossier_id: str, file_count_delta: int = 0, size_delta: int = 0):
        """Update dossier statistics incrementally."""
        if self.dry_run:
            logger.info("Dry run: would update dossier %s stats: count_delta=%d, size_delta=%d", 
                       dossier_id, file_count_delta, size_delta)
            return
            
        try:
            # Use update by query to increment counters
            script = {
                "source": """
                    if (params.file_count_delta != 0) {
                        ctx._source.file_count = Math.max(0, (ctx._source.file_count ?: 0) + params.file_count_delta);
                    }
                    if (params.size_delta != 0) {
                        ctx._source.total_size = Math.max(0, (ctx._source.total_size ?: 0) + params.size_delta);
                    }
                """,
                "params": {
                    "file_count_delta": file_count_delta,
                    "size_delta": size_delta
                }
            }
            
            query = {
                "script": script,
                "query": {
                    "term": {
                        "dossier_id.keyword": dossier_id
                    }
                }
            }
            
            result = self.es.update_by_query(
                index=ES_INDEX_DOSSIERS,
                body=query,
                refresh=True
            )
            
            updated_count = result.get("updated", 0)
            if updated_count > 0:
                logger.debug(f"Updated dossier {dossier_id} stats: {updated_count} records")
            
        except Exception as e:
            logger.error(f"Failed to update dossier stats for {dossier_id}: {e}")

    def document_exists(self, file_path: str) -> bool:
        """Check if a document with the given file path exists in ES."""
        if self.dry_run:
            return False
            
        try:
            query = {
                "query": {
                    "term": {
                        "filepath.keyword": file_path
                    }
                },
                "size": 0
            }
            
            result = self.es.search(index=self.index_docs, body=query)
            return result["hits"]["total"]["value"] > 0
            
        except Exception as e:
            logger.error(f"Failed to check document existence for {file_path}: {e}")
            return False

    def get_document_info(self, file_path: str) -> dict | None:
        """Get basic info about a document (dossier_id, file_size) for cleanup purposes."""
        if self.dry_run:
            return None
            
        try:
            query = {
                "query": {
                    "term": {
                        "filepath.keyword": file_path
                    }
                },
                "_source": ["dossier_id", "size"],
                "size": 1
            }
            
            result = self.es.search(index=self.index_docs, body=query)
            hits = result["hits"]["hits"]
            
            if hits:
                return hits[0]["_source"]
            return None
            
        except Exception as e:
            logger.error(f"Failed to get document info for {file_path}: {e}")
            return None

    def dossier_exists(self, dossier_id: str) -> bool:
        """Check if a dossier with the given dossier_id exists in ES."""
        if self.dry_run:
            return False
            
        try:
            result = self.es.exists(index=self.index_dossiers, id=dossier_id)
            return result
            
        except Exception as e:
            logger.error(f"Failed to check dossier existence for {dossier_id}: {e}")
            return False

    def index_new_dossier(self, dossier: dict):
        """Index a single new dossier."""
        logger.info(f"Indexing new dossier: {dossier.get('dossier_name')} - file_id: {dossier.get('file_id')}")
        
        if self.dry_run:
            logger.info(f"Dry run: would index new dossier {dossier.get('dossier_id')}")
            return
            
        try:
            # Normalize the created_datetime
            dossier_copy = dossier.copy()
            dossier_copy['created_datetime'] = self._normalize_timestamp(dossier.get("created_datetime"))
            dossier_copy['lastmodified_datetime'] = self._normalize_timestamp(dossier.get("lastmodified_datetime"))
            
            logger.debug(f"Dossier document to index: {dossier_copy}")
            
            action = {
                "_index": self.index_dossiers,
                "_id": dossier.get("dossier_id"),
                "_source": dossier_copy
            }
            
            helpers.bulk(self.es, [action])
            logger.info(f"Successfully indexed new dossier: {dossier.get('dossier_id')}")
            
        except Exception as e:
            logger.error(f"Failed to index new dossier {dossier.get('dossier_id')}: {e}")
            raise

    @staticmethod
    def _documents_mapping() -> dict:
        return {
            "settings": {
                "index": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                }
            },
            "mappings": {
                "properties": {
                    "paragraphs": {
                        "properties": {
                            "text": {"type": "text"},
                            "id": {"type": "long"},
                        }
                    },
                    "title": {"type": "text", "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}},
                    "raw_title": {"type": "text", "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}},
                    "retention_period": {"type": "text", "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}},
                    "nextcloud_id": {"type": "keyword"},
                    "url": {"type": "text", "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}},
                    "werkproces": {"type": "text", "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}},
                    "author": {"type": "text", "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}},
                    "author_id": {"type": "text", "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}},
                    "author_modified": {"type": "text", "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}},
                    "bewaartermijn": {"type": "text", "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}},
                    "created_date": {"type": "date"},
                    "datetime_published": {"type": "date"},
                    "description": {"type": "text", "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}},
                    "accessible_to_users": {"type": "text", "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}},
                    "dossier_id": {"type": "keyword"},
                    "dossier_name": {"type": "text", "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}},
                    "filepath": {"type": "text", "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}},
                    "drive_id": {"type": "text", "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}},
                    "lastmodifiedtime": {"type": "date"},
                    "filetype": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                    "full_text": {"type": "text"},
                    "keywords": {"type": "text", "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}},
                    "last_annotated": {"type": "date"},
                    "lastmodified_user_id": {"type": "text", "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}},
                    "needs_download": {"type": "keyword"},
                    "needs_annotation": {"type": "keyword"},
                    "number_pages": {"type": "integer"},
                    "size": {"type": "long", "fields": {"keyword": {"type": "keyword"}}},
                    "summary": {"type": "text", "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}},
                }
            },
        }

    @staticmethod
    def _dossiers_mapping() -> dict:
        return {
            "settings": {
                "index": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                }
            },
            "mappings": {
                "properties": {
                    "webURL": {"type": "text", "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}},
                    "file_id": {"type": "keyword"},  # Nextcloud file ID for the dossier folder
                    "nextcloud_id": {"type": "keyword"},
                    "members": {"type": "text", "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}},
                    "unopened": {"type": "boolean"},
                    "description": {"type": "text", "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}},
                    "dossier_id": {"type": "text", "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}},
                    "dossier_name": {"type": "text", "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}},
                    "owner_userid": {"type": "keyword"},
                    "created_datetime": {"type": "date"},
                    "lastmodified_datetime": {"type": "date"},
                    "type": {"type": "text", "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}}
                }
            },
        }
