from datetime import datetime

from elastic.elastic import ES, ES_INDEX

from utils.logging.logger import logger
from llm.llm_client import LLMClient
from llm.schemas.keywords_schema import keywords_schema
from asyncio import get_event_loop
import json


def update_elasticsearch_document(doc_id: str, update_body: dict) -> bool:
    try:
        ES.update(
            index=ES_INDEX,
            id=doc_id,
            body={"doc": update_body},
        )
        logger.info(f"Successfully updated document {doc_id} with {update_body}")
        return True
    except Exception as e:
        logger.error(f"Error updating document {doc_id}: {str(e)}")
        return False


def get_documents_to_annotate():
    """
    Get documents from Elasticsearch that need annotation.
    This includes:
    1. New documents (needs_annotation = "needed")
    """

    query = {
        "query": {
            "bool": {
                "should": [
                    {"term": {"needs_annotation": "needed"}},
                ]
            }
        }
    }

    query = {"query": {"bool": {"must_not": {"exists": {"field": "last_annotated"}}}}}

    response = ES.search(index=ES_INDEX, body=query, size=10000)

    return response.get("hits", {}).get("hits", [])


def mark_annotated(doc_id: str, markation: str = "annotated") -> bool:
    """Mark a document as annotated in Elasticsearch.
    Args:
        doc_id (str): The ID of the document to mark as annotated.
    Returns:
        bool: True if the document was successfully marked as annotated, False otherwise.
    """
    try:
        # Update the document to mark it as processed
        return update_elasticsearch_document(
            doc_id,
            {
                "needs_annotation": markation,
                "last_annotated": datetime.now().isoformat(),
            },
        )
    except Exception as e:
        logger.error(f"Error annotating document {doc_id}: {str(e)}")
        return False


def add_summary(doc_id: str, summary: str) -> bool:
    """Add a summary to a document in Elasticsearch.
    Args:
        doc_id (str): The ID of the document to update.
        summary (str): The summary to add to the document.
    Returns:
        bool: True if the summary was successfully added, False otherwise.
    """
    try:
        # Update the document with the summary
        return update_elasticsearch_document(
            doc_id,
            {"summary": summary},
        )
    except Exception as e:
        logger.error(f"Error adding summary to document {doc_id}: {str(e)}")
        return False


def add_bewaartermijn(doc_id: str, bewaartermijn: str = "10 jaar") -> bool:
    """Add a bewaartermijn to a document in Elasticsearch.
    Args:
        doc_id (str): The ID of the document to update.
        bewaartermijn (str): The bewaartermijn to add to the document.
    Returns:
        bool: True if the bewaartermijn was successfully added, False otherwise.
    """
    try:
        # Update the document with the bewaartermijn
        return update_elasticsearch_document(
            doc_id, {"retention_period": bewaartermijn, "werkprocess": "Process 5.2"}
        )
        # TODO: Add logic to infer the archiving date from the creation date of the document
    except Exception as e:
        logger.error(f"Error adding bewaartermijn to document {doc_id}: {str(e)}")
        return False


def add_keywords(doc_id: str, keywords: list) -> bool:
    """Add keywords to a document in Elasticsearch.
    Args:
        doc_id (str): The ID of the document to update.
        keywords (list): The list of keywords to add to the document.
    Returns:
        bool: True if the keywords were successfully added, False otherwise.
    """
    try:
        # Update the document with the keywords
        return update_elasticsearch_document(
            doc_id,
            {"keywords": keywords},
        )
    except Exception as e:
        logger.error(f"Error adding keywords to document {doc_id}: {str(e)}")
        return False


async def annotate_document(doc):
    """
    Annotate a single document.
    This is where you would implement your annotation logic.
    """

    doc_id = doc["_id"]
    logger.info(f"Annotating document {doc_id}")

    source = doc["_source"]
    # logger.debug(f"Document source: {source}")

    # TODO: Implement your annotation logic here
    # 1. Get text from ES document
    # 2. Extract keywords or entities from the text (e.g. using Mistral)
    # 3. Create summary of the document
    # 4. Infer "bewaartermijn", etc. from selectielijsten, etc.
    #   ▪ 047 Informatiecategorie (archiving)
    #   ▪ 048 Waardering (archiving)
    #   ▪ 049 Bewaartermijn (archiving)
    # 5. Update document with annotations

    # 1. Get text from ES document
    if isinstance(source, dict):
        content = ""
        if isinstance(source, dict):
            content = source.get("full_text", "")
    else:
        logger.error(
            f"Unexpected source format for document {doc_id}: Source is not a dictionary"
        )
        return False
    if not content:
        logger.warning(f"Document {doc_id} has no content (full_text) to annotate from")
        return False
    if len(content) < 200:
        logger.warning(
            f"Document {doc_id} has too little content ({len(content)} characters) to annotate from"
        )
        return mark_annotated(doc_id, "skipped__short_content")

    # 2. Extract keywords or entities from the text (e.g. using Mistral)

    # TODO: Currently zero shot. Potentially use a few shot approach with examples
    prompt = (
        "Given the following text, extract keywords about the text:\n\n"
        f"{content}\n\n"
        "Please provide a list of keywords in Dutch about the text. The keywords can be topics, themes, mentions, entities. Provide only key keywords and keep the amount limited (less than 8 keywords)."
    )

    llm_client = LLMClient()
    try:
        keyword_response = await llm_client.structured_invoke(
            keywords_schema, [("human", prompt)]
        )
        logger.info(f"LLM response for document {doc_id}: {keyword_response}")
        try:
            keyword_response = (
                json.loads(keyword_response)
                if isinstance(keyword_response, str)
                else keyword_response
            )
            if isinstance(keyword_response, dict):
                add_keywords(doc_id, keyword_response.get("keywords", []))
            else:
                logger.error(
                    f"Unexpected response format for document {doc_id}: {keyword_response}"
                )
                return False
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding LLM response for document {doc_id}: {str(e)}")
            return False
    except Exception as e:
        logger.error(f"Error invoking LLM for document {doc_id}: {str(e)}")
        return False

    # 3. Create summray of the document
    # TODO: Currently zero shot. Potentially use a few shot approach with examples
    summary_prompt = (
        "Given the following text, create a summary of the document:\n\n"
        f"{content}\n\n"
        "Please provide a concise  summary (no more than 600 characters) of the document in Dutch. Do not mention that the summary is in Dutch or how many characters it is. ONLY RETURN THE SUMMARY, NOTHING ELSE."
    )
    try:
        summary_response = await llm_client.invoke([("human", summary_prompt)])
        logger.info(f"LLM summary for document {doc_id}: {summary_response}")
        add_summary(doc_id, summary_response)

    except Exception as e:
        logger.error(f"Error invoking LLM for summary of document {doc_id}: {str(e)}")
        return False

    # 4. Infer "bewaartermijn", etc. from selectielijsten, etc.
    #   ▪ 047 Informatiecategorie (archiving)
    #   ▪ 048 Waardering (archiving)
    # V 10 na afhandeling dossier
    #   ▪ 049 Bewaartermijn (archiving)
    # 10 jaar

    try:
        add_bewaartermijn(doc_id, "10 jaar")

    except Exception as e:
        logger.error(f"Error adding bewaartermijn to document {doc_id}: {str(e)}")
        return False

    return mark_annotated(doc_id)


async def run_annotation_job():
    """
    Main function to run the annotation job.
    This can be called both from the scheduled job and programmatically.
    """
    logger.info("Starting annotation job")

    # Get documents that need annotation
    docs_to_annotate = get_documents_to_annotate()
    logger.info(f"Found {len(docs_to_annotate)} documents to annotate")

    # Process each document
    success_count = 0
    for doc in docs_to_annotate:
        doc_annotated = await annotate_document(doc)
        if doc_annotated:
            success_count += 1

    logger.info(
        f"Annotation job completed. Successfully annotated {success_count} out of {len(docs_to_annotate)} documents"
    )
    return success_count


if __name__ == "__main__":
    loop = get_event_loop()
    try:
        loop.run_until_complete(run_annotation_job())
    finally:
        loop.close()
