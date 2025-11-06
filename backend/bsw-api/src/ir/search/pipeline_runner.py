from sqlalchemy.orm import Session
import httpx

from api.models import ChatQuery
from ir.rag.interface import search_law_article, search_case_law, search_werk_instructie
from ir.graph.interface import query_taxonomy
from generation.interface import (
    get_answer_llm,
    get_main_query_prompt,
    extract_sources_in_answer,
    get_source_query_prompt,
)
from generation.output_schemas import (
    get_source_query_output_schema,
    get_main_query_output_schema,
)
from ir.db.interface import search_selectielijsten
from services.wegwijs_in_regels_search import get_user_info
from services.dossiers import get_dossier_from_id

from dependencies.auth import get_current_user
from utils.logging.logger import logger

LAWS = ["WOO", "AVG", "AWB", "Archiefwet"]


async def get_sources_list(
    message: str, user_info: dict, dossier: dict = None
) -> list[str]:
    if not dossier:
        dossier = {
            "dossier_name": "Geen specifieke casus/dossier beschikbaar",
            "description": "Er is geen aanvullende casuscontext beschikbaar; baseer het antwoord alleen op de gebruikersvraag en gebruikersinformatie.",
        }
    prompt = await get_source_query_prompt(
        user_query=message, user_info=user_info, dossier=dossier
    )
    schema = get_source_query_output_schema()
    response = await get_answer_llm(prompt, schema=schema)
    if not response:
        logger.warning("No relevant sources to use in query.")
        return []
    if "relevant_sources" not in response:
        logger.error("Response does not contain 'relevant_sources'.")
        return []
    relevant_sources = [
        source["source_id"] for source in response.get("relevant_sources", [])
    ]
    logger.info(f"Relevant sources extracted: {relevant_sources}")
    return relevant_sources


async def get_answer_to_query(
    user_query: str, data_sources: dict, user_info: dict, dossier: dict
) -> str:
    """Get answer to the users query using the LLM and the data sources"""
    prompt = await get_main_query_prompt(user_query, data_sources, user_info, dossier)
    output_schema = get_main_query_output_schema()
    response = await get_answer_llm(prompt, output_schema)
    response = response.get("answer", [])
    return response


async def run_pipeline(
    chat_query: ChatQuery,
    db: Session,
    http_client: httpx.AsyncClient,
    dossier_id: str = None,
) -> dict[str, dict]:
    """Run the pipeline for the given chat query"""

    user_info = get_user_info(kc_user_info=await get_current_user(), db=db)
    dossier = (
        get_dossier_from_id(dossier_id, user_info["user_id"]) if dossier_id else None
    )

    sources_to_query = await get_sources_list(
        chat_query.message, user_info, dossier=dossier
    )
    #TODO: remove once finished
    logger.info(f"Sources to query: {sources_to_query}")
    sources_to_query += [ "Jurisprudentie", "WOO-Werkinstructie", "Selectielijsten" ] 
    sources_to_query = list(set(sources_to_query))


    data_sources = await collect_data_sources(
        chat_query, sources_to_query, db, http_client
    )

    llm_response = await get_answer_to_query(
        chat_query.message, data_sources, user_info, dossier
    )

    referenced_response = await extract_sources_in_answer(
        llm_response, data_sources, sources_to_query
    )

    return referenced_response


async def collect_data_sources(
    chat_query: ChatQuery,
    sources_to_query: list,
    db: Session,
    http_client: httpx.AsyncClient,
) -> dict[str, list[str]]:
    """Collect data sources for the given chat query"""

    pipeline_data = {}

    # Step 1: Perform RAG search
    matching_sources = [source for source in sources_to_query if source in LAWS]
    if matching_sources:
        vector_search_result = await search_law_article(
            chat_query=chat_query, law_names=matching_sources
        )
        if vector_search_result:
            pipeline_data.update(vector_search_result)
            # law_uris, law_lido, law_jas = await query_graphs(pipeline_data.get("law_urls", []), http_client)
            # pipeline_data["law_uris"] = law_uris
            # pipeline_data["lido_results"] = law_lido
            # pipeline_data["jas_results"] = law_jas

    if "Jurisprudentie" in sources_to_query:
        case_law_search_result = await search_case_law(chat_query=chat_query)
        if case_law_search_result:
            pipeline_data.update(case_law_search_result)

    if "WOO-Werkinstructie" in sources_to_query:
        werk_instructie_search_result = await search_werk_instructie(
            chat_query=chat_query
        )
        if werk_instructie_search_result:
            pipeline_data.update(werk_instructie_search_result)

    # Step 2: Perform DB search to find relevant rows of selectielijsten based on user query
    if "Selectielijsten" in sources_to_query:
        selectielijsten_result = await search_selectielijsten(chat_query.message, db)
        if selectielijsten_result:
            pipeline_data["selectielijsten"] = selectielijsten_result

    # Step 3: Perform KG search to find relevant taxonomy terms
    taxonomy_result = await query_taxonomy(chat_query.message, http_client)
    if taxonomy_result:
        pipeline_data["taxonomy"] = taxonomy_result

    return pipeline_data
