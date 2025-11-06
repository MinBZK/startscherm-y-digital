import os
import uuid
import json
from azure.storage.blob import ContainerClient

from utils.logging.logger import logger
from elasticsearch_dsl import async_connections
from dependencies.elastic.ingest import chunk_document
from llm.llm_client import LLMClient
from api.models import (
    CaseLawDocumentIngest,
    LegalDocumentIngest,
    WerkInstructieDocumentIngest,
)
from ir.rag.models.model import (
    Chunk,
    LegalDocument,
    CaseLawChunk,
    CaseLawDocument,
    WerkInstructieChunk,
    WerkInstructieDocument,
)

# Get Elasticsearch hostname from environment variable
es_hostname = os.getenv("ES_HOSTNAME", "http://bsw-elasticsearch:9200")

def get_es_connection():
    """Get Elasticsearch connection, creating it if necessary"""
    try:
        # Try to get existing connection first
        return async_connections.get_connection()
    except:
        # Create connection if it doesn't exist
        async_connections.create_connection(hosts=[es_hostname])
        return async_connections.get_connection()

# Initialize connection but make it lazy
es = None

def get_es():
    """Get Elasticsearch connection lazily"""
    global es
    if es is None:
        es = get_es_connection()
    return es

llm_client = LLMClient()


async def bulk_ingest(documents, doc_type: str):
    async def make_async(iterable):
        for item in iterable:
            yield item

    if doc_type == "law":
        docs = [
            LegalDocument(
                title=title,
                body=body,
                url=url,
                date=date,
                law_name=law_name,
                meta={"id": str(uuid.uuid4())},
            )
            for title, body, url, date, law_name in documents
        ]
    elif doc_type == "case-law":
        docs = [
            CaseLawDocument(
                title=title,
                url=url,
                instantie=instantie,
                datum_uitspraak=datum_uitspraak,
                datum_publicatie=datum_publicatie,
                zaaknummer=zaaknummer,
                rechtsgebieden=rechtsgebieden,
                bijzondere_kenmerken=bijzondere_kenmerken,
                inhoudsindicatie=inhoudsindicatie,
                wetsverwijzingen=wetsverwijzingen,
                vindplaatsen=vindplaatsen,
                verrijkte_uitspraak=verrijkte_uitspraak,
                uitspraak=uitspraak,
                meta={"id": str(uuid.uuid4())},
            )
            for (
                title,
                url,
                instantie,
                datum_uitspraak,
                datum_publicatie,
                zaaknummer,
                rechtsgebieden,
                bijzondere_kenmerken,
                inhoudsindicatie,
                wetsverwijzingen,
                vindplaatsen,
                verrijkte_uitspraak,
                uitspraak,
            ) in documents
        ]
    elif doc_type == "werk-instructie":
        docs = [
            WerkInstructieDocument(
                title=title,
                subtitle=subtitle,
                publication_date=publication_date,
                url=url,
                body=body,
                meta={"id": str(uuid.uuid4())},
            )
            for (
                title,
                url,
                subtitle,
                publication_date,
                body,
            ) in documents
        ]
    else:
        raise ValueError(f"Invalid doc_type: {doc_type}")
    logger.info(f"Bulk ingesting {len(docs)} documents")

    if doc_type == "law":
        await LegalDocument.bulk(make_async(docs))
        chunks: list[Chunk] = []
        for doc in docs:
            logger.info(f"Chunking document {doc.meta.id}, {doc.title}")
            chunks.extend(
                [
                    Chunk(
                        document_id=doc.meta.id,
                        chunk_index=index,
                        chunk_text=chunk_text,
                        law_name=doc.law_name,
                    )
                    for index, chunk_text in enumerate(chunk_document(doc.body))
                ]
            )
    elif doc_type == "case-law":
        await CaseLawDocument.bulk(make_async(docs))
        chunks: list[CaseLawChunk] = []
        for doc in docs:
            logger.info(f"Chunking document {doc.meta.id}, {doc.title}")
            chunks.extend(
                [
                    CaseLawChunk(
                        document_id=doc.meta.id,
                        chunk_index=index,
                        chunk_text=chunk_text,
                        title=doc.title,
                    )
                    for index, chunk_text in enumerate(chunk_document(doc.uitspraak))
                ]
            )
    elif doc_type == "werk-instructie":
        await WerkInstructieDocument.bulk(make_async(docs))
        chunks: list[WerkInstructieChunk] = []
        for doc in docs:
            logger.info(f"Chunking document {doc.meta.id}, {doc.title}")
            chunks.extend(
                [
                    WerkInstructieChunk(
                        document_id=doc.meta.id,
                        chunk_index=index,
                        chunk_text=chunk_text,
                        title=doc.title,
                    )
                    for index, chunk_text in enumerate(chunk_document(doc.body))
                ]
            )

    embeddings = await llm_client.bulk_embed([chunk.chunk_text for chunk in chunks])
    for chunk, embedding in zip(chunks, embeddings):
        chunk.embedding = embedding

    if doc_type == "law":
        await Chunk.bulk(make_async(chunks))
    elif doc_type == "case-law":
        await CaseLawChunk.bulk(make_async(chunks))
    elif doc_type == "werk-instructie":
        await WerkInstructieChunk.bulk(make_async(chunks))


async def ingest_from_blob_storage(
    container_name: str,
    doc_type: str,
) -> int:
    logger.info(
        f"Starting ingest from blob storage for {doc_type=} in container {container_name=}"
    )
    container_client = ContainerClient.from_connection_string(
        os.getenv("AZURE_STORAGE_CONNECTION_STRING"), container_name
    )
    blobs = container_client.list_blobs()

    def _get_ingest_type(blob):
        if doc_type == "law":
            logger.info(f"Downloading blob {blob.name} for law-articles")
            return LegalDocumentIngest(
                **json.loads(container_client.download_blob(blob).readall())
            )
        elif doc_type == "case-law":
            logger.info(f"Downloading blob {blob.name} for case law")
            return CaseLawDocumentIngest(
                **json.loads(container_client.download_blob(blob).readall())
            )
        elif doc_type == "werk-instructie":
            logger.info(f"Downloading blob {blob.name} for werk-instructie")
            return WerkInstructieDocumentIngest(
                **json.loads(container_client.download_blob(blob).readall())
            )
        else:
            raise ValueError(f"Invalid doc_type: {doc_type}")

    json_documents = [
        _get_ingest_type(blob) for blob in blobs if blob.name.endswith(".json")
    ]

    if doc_type == "law":
        await bulk_ingest(
            (
                (doc.title, doc.body, doc.url, doc.date, doc.law_name)
                for doc in json_documents
            ),
            doc_type=doc_type,
        )
    elif doc_type == "case-law":
        await bulk_ingest(
            (
                (
                    doc.title,
                    doc.url,
                    doc.instantie,
                    doc.datum_uitspraak,
                    doc.datum_publicatie,
                    doc.zaaknummer,
                    doc.rechtsgebieden,
                    doc.bijzondere_kenmerken,
                    doc.inhoudsindicatie,
                    doc.wetsverwijzingen,
                    doc.vindplaatsen,
                    doc.verrijkte_uitspraak,
                    doc.uitspraak,
                )
                for doc in json_documents
            ),
            doc_type=doc_type,
        )
    elif doc_type == "werk-instructie":
        await bulk_ingest(
            (
                (doc.title, doc.url, doc.subtitle, doc.publication_date, doc.body)
                for doc in json_documents
            ),
            doc_type=doc_type,
        )
    else:
        raise ValueError(f"Invalid doc_type: {doc_type}")

    return len(json_documents)
