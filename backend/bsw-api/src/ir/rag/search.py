from utils.logging.logger import logger
from typing import List
from elasticsearch_dsl import Q


from ir.rag.models.model import Chunk, LegalDocument, CaseLawChunk, CaseLawDocument, WerkInstructieChunk, WerkInstructieDocument, VectorSearchCaseLawResult, VectorSearchResult, VectorSearchWerkInstructieResult
from llm.llm_client import LLMClient

SIMILARITY_THRESHOLD = 0.7
TOP_K_FINAL = 12
TOP_K_FINAL_LESS = 8

llm_client = LLMClient()

async def search(query: str, law_names: List[str]) -> VectorSearchResult:
    logger.info(f"Searching for: {query}")
    logger.info(f"Law names filter: {law_names}")
    query_embedding = await llm_client.get_embedding(query)

    should_queries = [Q("match", law_name=law) for law in law_names]

    filter_query = Q(
        "bool",
        should=should_queries,
        minimum_should_match=1
    )

    relevant_chunks = [
        chunk async for chunk in Chunk.search().knn(
            field="embedding",
            k=50,
            num_candidates=100,
            query_vector=query_embedding,
            similarity=SIMILARITY_THRESHOLD,
            filter=filter_query,
        ).iterate()
    ]
    logger.info(f"Found {len(relevant_chunks)} relevant chunks in function: {__name__}")

    relevant_chunks = relevant_chunks[:TOP_K_FINAL]
    relevant_doc_ids = list({chunk.document_id for chunk in relevant_chunks})
    if not relevant_doc_ids:
        logger.info("No relevant law documents found")
        return False

    relevant_docs = await LegalDocument.mget(relevant_doc_ids)

    logger.info(f"Found {len(relevant_docs)} relevant documents")
    for doc in relevant_docs:
        logger.info(
            f'Found document with the title: "{doc.title}", in the "{doc.law_name}" law.\nURL: {doc.url}'
        )

    return VectorSearchResult(
        law_documents=[doc.body for doc in relevant_docs],
        law_chunks=[
            [
                str(chunk.chunk_text)
                for chunk in relevant_chunks
                if chunk.document_id == doc_id
            ]
            for doc_id in relevant_doc_ids
        ],
        law_laws=[doc.law_name for doc in relevant_docs],
        law_titles=[doc.title for doc in relevant_docs],
        law_urls=[doc.url for doc in relevant_docs],
    )


async def search_case_laws(query: str) -> VectorSearchCaseLawResult:
    logger.info(f"Searching for: {query}")

    query_embedding = await llm_client.get_embedding(query)

    relevant_chunks = [
        chunk
        async for chunk in CaseLawChunk.search()
        .knn(
            field="embedding",
            k=50,
            num_candidates=100,
            query_vector=query_embedding,
            similarity=SIMILARITY_THRESHOLD,
        )
        .iterate()
    ]
    logger.info(f"Found {len(relevant_chunks)} relevant chunks in function: {__name__}")

    relevant_chunks = relevant_chunks[:TOP_K_FINAL_LESS]
    relevant_doc_ids = list({chunk.document_id for chunk in relevant_chunks})
    if not relevant_doc_ids:
        logger.info("No relevant case law documents found")
        return False

    relevant_docs = await CaseLawDocument.mget(relevant_doc_ids)

    logger.info(f"Found {len(relevant_docs)} relevant documents")
    for doc in relevant_docs:
        logger.info(
            f'Found document with the title: "{doc.title}", in the case law with case number: "{doc.zaaknummer}".\nURL: {doc.url}'
        )

    return VectorSearchCaseLawResult(
        cl_documents=[doc.uitspraak for doc in relevant_docs],
        cl_chunks=[
            [
                str(chunk.chunk_text)
                for chunk in relevant_chunks
                if chunk.document_id == doc_id
            ]
            for doc_id in relevant_doc_ids
        ],
        cl_case_numbers=[doc.zaaknummer for doc in relevant_docs],
        cl_titles=[doc.title for doc in relevant_docs],
        cl_inhoudsindicaties=[doc.inhoudsindicatie for doc in relevant_docs],
        cl_date_uitspraken=[doc.datum_uitspraak for doc in relevant_docs],
        cl_urls=[doc.url for doc in relevant_docs],
    )


async def search_werk_instructies(query: str) -> VectorSearchWerkInstructieResult:
    logger.info(f"Searching for: {query}")

    query_embedding = await llm_client.get_embedding(query)

    relevant_chunks = [
        chunk
        async for chunk in WerkInstructieChunk.search()
        .knn(
            field="embedding",
            k=50,
            num_candidates=100,
            query_vector=query_embedding,
            similarity=SIMILARITY_THRESHOLD,
        )
        .iterate()
    ]
    logger.info(f"Found {len(relevant_chunks)} relevant chunks in function: {__name__}")

    relevant_chunks = relevant_chunks[:TOP_K_FINAL_LESS]
    relevant_doc_ids = list({chunk.document_id for chunk in relevant_chunks})
    if not relevant_doc_ids:
        logger.info("No relevant werk instructie documents found")
        return False

    relevant_docs = await WerkInstructieDocument.mget(relevant_doc_ids)

    logger.info(f"Found {len(relevant_docs)} relevant documents")
    for doc in relevant_docs:
        logger.info(
            f'Found document with the title: "{doc.title}", in the werk instructie woo.\nURL: {doc.url}'
        )

    return VectorSearchWerkInstructieResult(
        wi_documents=[doc.body for doc in relevant_docs],
        wi_chunks=[
            [
                str(chunk.chunk_text)
                for chunk in relevant_chunks
                if chunk.document_id == doc_id
            ]
            for doc_id in relevant_doc_ids
        ],
        wi_titles=[doc.title for doc in relevant_docs],
        wi_urls=[doc.url for doc in relevant_docs],
    )
