from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import re
import asyncio
from collections import defaultdict
import traceback

from llm.llm_client import LLMClient
from ir.search.utils import (
    get_sources_with_ids_list,
    map_paragraph_sources,
    consolidate_source_dict,
)
from generation.output_schemas import get_paragraphwise_source_schema, get_taxonomy_extraction_schema, get_source_extraction_schema
from utils.logging.logger import logger

llm_client = LLMClient()
LAWS = ["WOO", "AVG", "AWB", "Archiefwet"]


base_path = Path(__file__).parent / "prompts"
JINJA_ENV = Environment(
    enable_async=True, loader=FileSystemLoader(base_path)
)
PROMPT_TEMPLATE = JINJA_ENV.get_template("prompt_template.jinja2")
CONTEXT = "Een ambtenaar van het Nederlandse ministerie van Infrastructuur en Waterstaat met een juridische achtergrond behandelt een verzoek. De ambtenaar wil bepalen of de gezochte informatie verstrekt kan worden onder de Wet open overheid (WOO), of alle relevante bestanden met betrekking tot de vraag in het archief aanwezig zijn op basis van de Archiefwet 1995 en selectielijsten, en hoe er moet worden omgegaan met persoonsgegevens in de verstrekte informatie, rekening houdend met de Uitvoeringswet Algemene Verordening Gegevensbescherming."


async def get_answer_llm(prompt: str, schema: dict = None) -> dict[str, str]:
    """Invoke LLM with prompt"""
    model = llm_client.get_model()
    if schema:
        # NOTE: Only works for Mistral model currently!
        model = model.with_structured_output(schema)
    response = await model.ainvoke([("human", prompt)])
    logger.info(response)
    return response


async def get_main_query_prompt(question: str, data: dict, user_info: dict, dossier: dict) -> str:
    try:
        rendered_template = await PROMPT_TEMPLATE.render_async(
            question=question,
            user_info=user_info,
            dossier=dossier,
            context=CONTEXT,
            law_sources=zipped_enum(["law_documents", "law_titles", "law_laws"], data), # "law_uris", "lido_results", "jas_results"
            case_law_sources=zipped_enum(["cl_titles", "cl_chunks", "cl_inhoudsindicaties", "cl_date_uitspraken", "cl_case_numbers",], data),
            werkinstructies=zipped_enum(["wi_titles", "wi_chunks"], data),
            selectielijsten=data.get("selectielijsten"),
            taxonomy=data.get("taxonomy"),
        )
        logger.debug(f"Rendered prompt template for main query: {rendered_template}")
        return rendered_template
    except Exception as e:
        logger.error(f"An error occurred while rendering the prompt template: {e}")
        raise

def get_paragraphs(response: str) -> list[str]:
    """Extract paragraphs from LLM response"""

    def clean_response(response: str) -> str:
        """Clean response from any special characters except comma, dot, and colon"""
        # cleaned = re.sub(r"[^\w\s,.:*<>-]", "", response)
        return response.strip()   

    raw_paragraphs = response.split("\n\n")
    cleaned_response = [clean_response(p) for p in raw_paragraphs if p.strip()]

    return cleaned_response 

async def get_source_extraction_prompt_and_schema(source_name: str, relevant_paragraphs: list, data: dict) -> dict:
    """Generate template for source extraction in per paragraph"""
    try:
        if source_name == "taxonomy":
            SOURCE_EXTRACTION_TEMPLATE = JINJA_ENV.get_template("taxonomie_extraction.jinja2")
            rendered_template = await SOURCE_EXTRACTION_TEMPLATE.render_async(
                relevant_paragraphs=relevant_paragraphs,
                taxonomy=data.get("taxonomy"),
            )
            logger.debug(f"Rendered taxonomy extraction template: {rendered_template}")
            schema = get_taxonomy_extraction_schema()
            return rendered_template, schema
        else:
            SOURCE_EXTRACTION_TEMPLATE = JINJA_ENV.get_template("source_extraction.jinja2")
            rendered_template = await SOURCE_EXTRACTION_TEMPLATE.render_async(
                relevant_paragraphs=relevant_paragraphs,
                law_sources=zipped_enum(["law_documents", "law_titles", "law_laws"], data) if source_name == "LAWS" else [],
                case_law_sources=zipped_enum(["cl_titles", "cl_chunks", "cl_inhoudsindicaties", "cl_date_uitspraken", "cl_case_numbers"], data) if source_name == "Jurisprudentie" else [],
                werkinstructies=zipped_enum(["wi_titles", "wi_chunks"], data) if source_name == "WOO-Werkinstructie" else [],
                selectielijsten=data.get("selectielijsten") if source_name == "Selectielijsten" else [],
            )
            logger.debug(f"Rendered source extraction template for source name {source_name}: {rendered_template}")
            schema = get_source_extraction_schema()
            return rendered_template, schema
    except Exception as e:
        logger.error(f"An error occurred while rendering the source prompt template: {e}")
        raise


async def get_source_query_prompt(user_query: str, user_info:dict, dossier: dict) -> str:
    """Generate template for source query"""
    try:
        SOURCE_QUERY_TEMPLATE = JINJA_ENV.get_template("gate.jinja2")
        rendered_template = await SOURCE_QUERY_TEMPLATE.render_async(
            user_query=user_query,
            user_info=user_info,
            dossier=dossier,
        )
        logger.debug(f"Rendered prompt template: {rendered_template}")

        return rendered_template
    except Exception as e:
        logger.error(f"An error occurred while rendering the source query template: {e}")
        raise

async def process_sources(source_name: str, data: dict, indices: list, source_paragraphs: list[tuple]) -> dict:
    source_dict = {}

    relevant_paragraphs = [
        paragraph for paragraph in source_paragraphs
        if paragraph[0] in indices] if source_name != "taxonomy" else source_paragraphs

    prompt, schema = await get_source_extraction_prompt_and_schema(source_name, relevant_paragraphs, data)
    source_response = await get_answer_llm(prompt, schema)

    try:
        source_dict[source_name] = source_response["paragraphs"]
    except TypeError as e:
        logger.error(f"TypeError while processing sources for {source_name}: {e}")
        source_dict[source_name] = []

    return source_dict


async def get_source_per_paragraph(paragraphs: list, sources_lst: list) -> dict:
    """Get source per paragraph"""
    try:
        schema = get_paragraphwise_source_schema(allowed_sources=sources_lst)
        logger.info("Generating source per paragraph template")
        SOURCE_PER_PARAGRAPH_TEMPLATE = JINJA_ENV.get_template("source_per_paragraph.jinja2")
        rendered_template = await SOURCE_PER_PARAGRAPH_TEMPLATE.render_async(
            paragraphs=paragraphs,
            sources=sources_lst
        )
        logger.debug(f"Rendered source per paragraph template: {rendered_template}")
        llm_response = await get_answer_llm(rendered_template, schema)
        res = llm_response["paragraphs"]
        source_paragraph_map = defaultdict(list)  # Initialize with list to avoid KeyError

        for paragraph in res:
            index = paragraph["paragraph_index"]
            for src in paragraph.get("relevant_sources", []):
                source_name = src.get("source_names")
                if source_name in sources_lst:
                    if source_name in LAWS:
                        if index not in source_paragraph_map["LAWS"]:
                            source_paragraph_map["LAWS"].append(index)
                    else:
                        source_paragraph_map[source_name].append(index)
            for src in paragraph.get("unlisted_sources", []):  # Assume that if another source is mentioned it got it from de Jurisprudentie
                if (src not in LAWS) and (index not in source_paragraph_map["Jurisprudentie"]):
                    source_paragraph_map["Jurisprudentie"].append(index)
        source_paragraph_map["taxonomy"] = []  # Add taxonomy key as it also needs to be processed
        return source_paragraph_map

    except Exception as e:
        logger.error(f"An error occurred while rendering the source per paragraph template: {e}")
        raise


async def extract_sources_in_answer(response: str, data: dict, sources_to_query: list) -> dict[list[dict]]:
    """Extract sources from each paragraph in the LLM response using LLM"""
    try:
        logger.info("Extracting sources used in LLM response")
        paragraphs = get_paragraphs(response)
        indexed_paragraphs = [(index, element) for index, element in enumerate(paragraphs)]

        sources_lst = get_sources_with_ids_list(data)

        sources_per_paragraph = await get_source_per_paragraph(paragraphs, sources_to_query) 


        # prepared_sources = prepare_sources(data)
        extracted_sources = await asyncio.gather(
                *[process_sources(source_name, data, indices, indexed_paragraphs) for source_name, indices in sources_per_paragraph.items()]
            )

        merged_sources_dict = {}
        for d in extracted_sources:
            merged_sources_dict.update(d)

        sorted_paragraph_sources = merge_dicts_by_paragraph(merged_sources_dict, indexed_paragraphs)

        paragraphs_with_sources = []
        for paragraph in sorted_paragraph_sources:
            paragraphs, sources_lst = map_paragraph_sources(paragraph, sources_lst)
            paragraphs_with_sources.append(paragraphs)

        logger.info("Sources extracted successfully")

        sources_lst = consolidate_source_dict(sources_lst)
        response_dict = {
            "answer": {"text": paragraphs_with_sources, "sources": sources_lst}
        }
        return response_dict
    except Exception as e:
        logger.error(
            f"An error occurred while extracting sources used in LLM response: {e},\n\nTraceback: {traceback.print_exc()}"
        )


def merge_dicts_by_paragraph(extracted_sources: dict, indexed_paragraphs: list[tuple]) -> list[dict]:
    paragraph_w_sources = []
    
    for i, p in enumerate(indexed_paragraphs):
        paragraph_source_dict = {
            "paragraph_index": i,
            "paragraph": p[1],
            "sources": {} 
        }
        for key, lst in extracted_sources.items():
            for k, v in enumerate(lst):
                if v["paragraph_index"] == i:
                    if key == "taxonomy":
                        if "updated_paragraph" in v:
                            paragraph_source_dict["paragraph"] = v["updated_paragraph"]
                            paragraph_source_dict["sources"][key] = v["taxonomie_term_index"]
                    else:
                        paragraph_source_dict["sources"][key] = v["sources"]
                
        paragraph_w_sources.append(paragraph_source_dict)            
    return paragraph_w_sources


def zipped_enum(keys: list, data: dict):
    if all(key in data for key in keys):
        return list(enumerate(zip(*(data[key] for key in keys)), start=0))
    return None
