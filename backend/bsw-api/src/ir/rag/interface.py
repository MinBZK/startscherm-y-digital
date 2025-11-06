from utils.logging.logger import logger
from typing import Union

from ir.rag.search import search, search_case_laws, search_werk_instructies
from ir.rag.models.model import VectorSearchCaseLawResult, VectorSearchResult, VectorSearchWerkInstructieResult
from api.models import ChatQuery


async def search_law_article(chat_query: ChatQuery, law_names: list) -> Union[VectorSearchResult, str]:
    """
    Perform a search for relevant law articles based on the chat query
    """
    try:
        logger.debug("Searching the vector database for relevant law articles")
        logger.debug(f"Chat query: {chat_query.message}")

        search_result = await search(chat_query.message, law_names=law_names)
        if not search_result:
            return False

        logger.info(f"Found {len(search_result.law_urls)} relevant law articles")
        return search_result.model_dump()
    except Exception as e:
        logger.error(f"Error during search of law article: {e}")
        return False


async def search_case_law(chat_query: ChatQuery) -> VectorSearchCaseLawResult | None | str:
    """
    Perform a search for relevant case law judgments based on the chat query
    """
    try:
        logger.info("Searching the vector database for relevant case law judgments")

        search_result = await search_case_laws(chat_query.message)
        if not search_result:
            return False

        logger.info(f"Found {len(search_result.cl_urls)} relevant case law judgments.")
        return search_result.model_dump()
    except Exception as e:
        logger.error(f"Error during search of case law: {e}")
        return False


async def search_werk_instructie(chat_query: ChatQuery) -> VectorSearchWerkInstructieResult | None | str:
    """
    Perform a search for relevant law articles based on the chat query
    """
    try:
        logger.info("Searching the vector database for relevant work instructions")

        search_result = await search_werk_instructies(chat_query.message)
        if not search_result:
            return False

        logger.info(f"Found {len(search_result.wi_urls)} relevant work instructions.")
        return search_result
    except Exception as e:      
        logger.error(f"Error during search of werkinstructie: {e}")
        return False
