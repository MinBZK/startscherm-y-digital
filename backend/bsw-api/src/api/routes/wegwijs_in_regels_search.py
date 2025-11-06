from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ir.search.ingest import get_es
from ir.rag.models.model import create_indices
from ir.search.ingest import ingest_from_blob_storage
from ir.graph.fuseki import ping_fuseki, ingest_graph_from_blob_storage
from ir.graph.interface import query_graph_lawuri, query_taxonomy
from api_utils.clients.httpx_client import get_http_client
from api.models import (
    GraphFromBlobUpload,
    GraphLawQuery,
    GraphTaxonomyQuery,
    CSVFile,
    ChatQuery,
)
from ir.db.database import get_db
from ir.db.data_processing import upload_csv_to_db
from ir.rag.formulator import formulate_rag_answer
from ir.rag.search import search
from llm.llm_client import LLMClient
from utils.logging.logger import logger


app = APIRouter(prefix="/system", tags=["system"])

llm_client = LLMClient()


@app.get("/health")
async def health(http_client=Depends(get_http_client)):
    # Check Elasticsearch connection status
    es_status = "down"
    try:
        es = get_es()
        es_status = "running" if await es.ping() else "down"
    except Exception as e:
        logger.warning(f"Elasticsearch health check failed: {e}")
        es_status = "down"
    
    # Check Fuseki connection status
    fuseki_status = "down"
    try:
        fuseki_status = "running" if await ping_fuseki(http_client) else "down"
    except Exception as e:
        logger.warning(f"Fuseki health check failed: {e}")
        fuseki_status = "down"
    
    return {
        "status_app": "running",
        "status_fuseki": fuseki_status,
        "status_elasticsearch": es_status,
    }


@app.get("/create-es-indices")
async def create_es_index():
    """
    Create Elasticsearch indices
    """
    await create_indices()
    return {"message": "Indices created"}


@app.get("/ingest-es-from-blob-storage")
async def ingest_es_blob_storage():
    """
    Trigger ES ingest from blob storage
    """
    n_docs = await ingest_from_blob_storage(
        container_name="legal-docs",
        doc_type="law",
    )
    return {"message": f"Ingested {n_docs} from blob storage"}


@app.get("/ingest-case-law-from-blob-storage")
async def ingest_case_law_blob_storage():
    """
    Trigger case law ingest from blob storage
    """
    n_docs = await ingest_from_blob_storage(
        container_name="bsw-case-laws",
        doc_type="case-law",
    )
    return {"message": f"Ingested {n_docs} from blob storage"}


@app.get("/ingest-werk-instructie-from-blob-storage")
async def ingest_werk_instructie_blob_storage():
    """
    Trigger werk instructie ingest from blob storage
    """
    n_docs = await ingest_from_blob_storage(
        container_name="werk-instructie",
        doc_type="werk-instructie",
    )
    return {"message": f"Ingested {n_docs} from blob storage"}


@app.post("/upload-graph")
async def upload_graph(
    graph: GraphFromBlobUpload, http_client=Depends(get_http_client)
):
    """
    Upload graph
    """
    logger.info(f"Retrieving graph {graph.blob_name} and uploading to Fuseki")

    result = await ingest_graph_from_blob_storage(graph.blob_name, http_client)
    return {"message": result}


@app.get("/graph-query-lawuri")
async def graph_query_graph_lawuri(
    query: GraphLawQuery, http_client=Depends(get_http_client)
):
    """Queries a graph in Fuseki based on a lawuri

    Args:
        query (GraphLawQuery): str: lawuri, str: graph name
        http_client (_type_, optional): _description_. Defaults to Depends(get_http_client).
    """
    logger.info(
        f"Querying graph http://example.org/{query.graph.lower()} for lawuri {query.lawuri}"
    )

    # Query the graph
    response = await query_graph_lawuri(query.lawuri, query.graph, http_client)
    return {"response": response}


@app.get("/query-taxonomy")
async def graph_query_taxonomy(
    query: GraphTaxonomyQuery,
    http_client=Depends(get_http_client),
):
    """
    .
    """
    logger.info(f"Querying graph {query.graph}.")

    # Query the graph
    response = await query_taxonomy(
        query.user_query,
        query.graph,
        http_client,
    )
    return {"response": response}


@app.post("/upload-csv")
def upload_csv(csv_file: CSVFile, db: Session = Depends(get_db)):
    """Upload csv file to database"""

    logger.info(f"Uploading CSV file {csv_file.file_name} to database")

    response = upload_csv_to_db(csv_file.file_name, db)

    logger.info(f"CSV file {csv_file.file_name} successfully uploaded to database")
    return {"message": response}


@app.post("/chat-rag")
async def chat_rag(chat_query: ChatQuery) -> str:
    """RAGchat

    Args:
        chat_query (ChatQuery): Chat query

    Returns:
        str: RAG response message
    """
    search_result = await search(chat_query.message, law_names=[])
    if len(search_result.law_documents) == 0:
        return "Ik heb geen relevante informatie kunnen vinden om deze vraag te beantwoorden."
    try:
        answer, source_index = await formulate_rag_answer(
            chat_query.message, search_result
        )
    except:
        return "Deze vraag kan ik helaas nog niet beantwoorden."
    if source_index is not None and source_index < len(search_result.law_documents):
        return f"""{answer}\n\nVoornaamste bron: {search_result.law_laws[source_index]}, {search_result.law_titles[source_index]}\nLink: {search_result.law_urls[source_index]}"""
    return answer


@app.post("/chat-llm")
async def chat_llm(chat_query: ChatQuery):
    messages = [
        (
            "system",
            """Je bent een behulpzame assistent die vragen over de informatiewetten kan beantwoorden.""",
        ),
        ("human", chat_query.message),
    ]
    response = await llm_client.invoke(messages)
    logger.info(response)
    return {"message": response}
