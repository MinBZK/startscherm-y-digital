import ast
import re
from collections import defaultdict, deque
import datetime
from typing import Tuple
import json
from utils.logging.logger import logger
import uuid
import traceback



def consolidate_source_dict(data: dict) -> dict:
    """Remove indices from the source extraction dictionary and consilidate to one dictionary"""
    try:
        sources = []
        if "selectielijsten" in data:
            for dct in data["selectielijsten"]:
                dct["value"].pop("indices", None)
                sources.append(dct)

        law_type = ["laws", "case_laws"]
        for key in law_type:
            if key in data:
                for dct in data[key]:
                    dct["value"].pop("index", None)
                    sources.append(dct)

        if "werkinstructies" in data:
            for dct in data["werkinstructies"]:
                dct["value"].pop("index", None)
                sources.append(dct)
        if "taxonomy" in data:
            for dct in data["taxonomy"]:
                dct["value"].pop("index", None)
                sources.append(dct)

        return sources
    except Exception as e:
        logger.error(f"An error occurred while consolidating source dict: {e}")


def map_paragraph_sources(paragraph_dict: dict, sources_lst: dict
) -> dict:
    try:
        if not paragraph_dict["sources"]:
            return {"paragraph": paragraph_dict["paragraph"], "sources": []}, sources_lst
        else:
            sources = []
            paragraph, sources_lst = map_taxonomy_terms(paragraph_dict, sources_lst)

            SOURCE_TYPES = [
                ("Selectielijsten", lambda d, s: map_selectielijsten_sources(d, s)),
                ("LAWS", lambda d, s: map_law_sources(d, s)),
                ("Jurisprudentie", lambda d, s: map_case_law_sources(d, s)),
                ("WOO-Werkinstructie", lambda d, s: map_werkinstructie_sources(d, s)),
            ]

            for key, processor in SOURCE_TYPES:
                if key not in paragraph_dict["sources"]:
                    continue

                source_ids, sources_lst = processor(paragraph_dict["sources"][key], sources_lst)
                sources.extend(source_ids)

            # Remove duplicates
            sources = list(dict.fromkeys(sources))

            paragraph_sources_dict = {"paragraph": paragraph, "sources": [str(u) for u in sources]}
            return paragraph_sources_dict, sources_lst
    except Exception as e:
        logger.error(f"An error occurred while mapping sources in paragraph: {e},\n\nTraceback: {traceback.format_exc()}")
        raise


def map_selectielijsten_sources(
    index_lst: dict, sources_lst: dict
) -> Tuple[list, dict]:
    """Identifying selectielijsten sources in the paragraph and updating isSource to True for used sources."""
    try:
        logger.info("Mapping selectielijsten sources in paragraph")
        if index_lst:
            selectielijsten_sources = []
            for idx in index_lst:
                found = False
                for i, dct in enumerate(sources_lst["selectielijsten"]):
                    if idx in dct["value"]["indices"]:
                        id = dct["id"]
                        selectielijsten_sources.append(id)
                        index_in_indices = dct["value"]["indices"].index(idx)
                        sources_lst["selectielijsten"][i]["value"]["rows"][
                            index_in_indices
                        ]["isSource"] = True
                        found = True
                        break
                if not found:
                    logger.warning(f"Index {idx} not found in any selectielijsten group")

            return selectielijsten_sources, sources_lst
        else:
            return [], sources_lst
    except Exception as e:
        logger.error(f"An error occurred while mapping selectielijsten sources: {e}")


def map_law_sources(index_lst: dict, sources_lst: dict) -> Tuple[list, dict]:
    """Identifying law and case law sources in the paragraph and updating isSource to True for used sources."""
    try:
        logger.info("Mapping law sources in paragraph")
        if index_lst:
            law_sources = []
            for idx in index_lst:
                if idx >= len(sources_lst["laws"]):
                    logger.warning(f"Index {idx} is out of range for laws list")
                    continue
                assert sources_lst["laws"][idx]["value"]["index"] == idx
                id = sources_lst["laws"][idx]["id"]
                law_sources.append(id)
                sources_lst["laws"][idx]["value"]["isSource"] = True
            else:
                logger.info("No laws source found in paragraph")

            return law_sources, sources_lst
        else:
            return [], sources_lst
    except Exception as e:
        logger.error(f"An error occurred while mapping law sources: {e}")

def map_case_law_sources(index_lst: dict, sources_lst: dict) -> Tuple[list, dict]:
    """Identifying law and case law sources in the paragraph and updating isSource to True for used sources."""
    try:
        logger.info("Mapping case law sources in paragraph")
        if index_lst:
            law_sources = []
            for idx in index_lst:
                if idx >= len(sources_lst["case_laws"]):
                    logger.warning(f"Index {idx} is out of range for case_laws list")
                    continue
                assert sources_lst["case_laws"][idx]["value"]["index"] == idx
                id = sources_lst["case_laws"][idx]["id"]
                law_sources.append(id)
                sources_lst["case_laws"][idx]["value"]["isSource"] = True
            else:
                logger.info("No case laws source found in paragraph")

            return law_sources, sources_lst
        else:
            return [], sources_lst
    except Exception as e:
        logger.error(f"An error occurred while mapping case law sources: {e}")


def map_werkinstructie_sources(index_lst: dict, sources_lst: dict) -> Tuple[list, dict]:
    """Identifying werkinstructie sources in the paragraph and updating isSource to True for used sources."""
    try:
        logger.info("Mapping werkinstructie sources in paragraph")
        if index_lst:
            werkinstructie_sources = []
            for idx in index_lst:
                # idx = 0 #NOTE: werk instructie document too big, it often gets it wrong, althought there is currently only one
                assert sources_lst["werkinstructies"][idx]["value"]["index"] == idx
                id = sources_lst["werkinstructies"][idx]["id"]
                werkinstructie_sources.append(id)
                sources_lst["werkinstructies"][idx]["value"]["isSource"] = True

            else:
                logger.info("No werkinstructie source found in paragraph")
            return werkinstructie_sources, sources_lst
        else:
            return [], sources_lst
    except Exception as e:
        logger.error(f"An error occurred while mapping werkinstructie sources: {e}")


def map_taxonomy_terms(paragraph_dict, sources_lst) -> Tuple[str, dict]:
    """Source indices to the unique source indices in sources dict and update isSource for used sources.
    Return paragraph with updated source id in angle brackets, eg. <persoonsgegevens> -> <source_5>
    """
    try:
        logger.info("Mapping taxonomy terms in paragraph")
        paragraph = paragraph_dict["paragraph"]

        if "taxonomy" in paragraph_dict["sources"] and "taxonomy" in sources_lst:
            taxonomy_dict = paragraph_dict["sources"]["taxonomy"]

            for i, term_index in enumerate(taxonomy_dict["term_index"]):
                if f"<{term_index}>" not in paragraph:
                    logger.info(f"Term index <{term_index}> not found in paragraph: {paragraph}")
                    continue
                else:
                    logger.info("Mapping taxonomy term in paragraph")
                    context_index = taxonomy_dict["context_index"][i]

                    term_value = sources_lst["taxonomy"][term_index]["value"]

                    id = term_value["context"][context_index]["id"]

                    sources_lst["taxonomy"][term_index]["value"]["context"][context_index][
                        "isSource"
                    ] = True
                    paragraph = re.sub(
                        rf"<{term_index}>", f"<{id}>", paragraph
                    )
                # Remove brackets with numbers not in TERM_INDEX
                paragraph = re.sub(
                    r"<(\d+)>",
                    lambda match: "" if int(match.group(1)) not in taxonomy_dict["term_index"] else match.group(0),
                    paragraph,
                )
        else:
            paragraph = re.sub(r"<[^>]+>", "", paragraph)
            if "taxonomy" in sources_lst:
                logger.info("No taxonomy term found in paragraph")
            else:
                logger.info("taxonomy not found in sources_lst")
        return paragraph, sources_lst
    except Exception as e:
        logger.error(f"An error occurred while mapping taxonomy terms: {e}, paragraph: {paragraph_dict},\n\nTraceback: {traceback.format_exc()}")




def get_sources_with_ids_list(data: dict) -> dict:
    """Generate a dictionary of sources with unique IDs"""
    try:
        sources_dict = {}
        SOURCE_TYPES = [
            ("selectielijsten", lambda d: process_selectielijst(d)),
            ("law_documents", lambda d: process_laws(d)),
            ("cl_documents", lambda d: process_laws(d, is_caselaw=True)),
            ("wi_titles", lambda d: process_werkinstructies(d)),
            ("taxonomy", lambda d: process_taxonomy(d)),
        ]
        for key, processor in SOURCE_TYPES:
            if key not in data:
                continue

            data_type, value = processor(data)
            sources_dict[data_type] = value

        return sources_dict

    except Exception as e:
        logger.error(f"An error occurred while generating source IDs: {e}")
        raise


def process_laws(data: dict, is_caselaw: bool = False) -> list[dict]:
    """Process laws data and case law data into output format"""
    try:
        if is_caselaw:
            case_laws = []
            for i, _ in enumerate(data["cl_titles"]):
                law_dict = {
                    "isSource": False,
                    "chunks": data["cl_chunks"][i],
                    "title": data["cl_titles"][i],
                    "inhoudsindicatie": data["cl_inhoudsindicaties"][i],
                    "date_uitspraak": data["cl_date_uitspraken"][i].isoformat(), #if isinstance(data["cl_date_uitspraak"][i], datetime.date) else data["cl_date_uitspraak"][i],
                    "url": data["cl_urls"][i],
                    "lido": {}, 
                    "index": i,
                }
                case_laws.append({"id": uuid.uuid4(), "type": "case_law", "value": law_dict})
            return "case_laws", case_laws
        else:
            laws = []
            for i, law in enumerate(data["law_laws"]):
                law_dict = {
                    "isSource": False,
                    "document": data["law_documents"][i],
                    "title": data["law_titles"][i],
                    "law": law,
                    "url": data["law_urls"][i],
                    "lido": {},
                    "index": i,
                }
                laws.append({"id": uuid.uuid4(), "type": "law", "value": law_dict})
            return "laws", laws
    except Exception as e:
        logger.error(f"An error occurred while processing laws data: {e}")
        return None


def process_werkinstructies(data: dict) -> list[dict]:
    try:
        werkinstructies = []
        for i, _ in enumerate(data["wi_titles"]):
            werkinstructie_dict = {
                "isSource": False,
                # "document": data["wi_documents"][i],
                "chunks": data["wi_chunks"][i],
                "title": data["wi_titles"][i],
                "url": data["wi_urls"][i],
                "index": i,
            }
            werkinstructies.append(
                    {"id": uuid.uuid4(), "type": "werkinstructie", "value": werkinstructie_dict}
                )
        return "werkinstructies", werkinstructies
    except Exception as e:
        logger.error(f"An error occurred while processing werkinstructie data: {e}")
        return None


def process_taxonomy(data) -> list[dict]:
    """Process taxonomy data into output format"""
    try:
        taxonomy = []

        for i, term in enumerate(data["taxonomy"]):
            term_dict = {
                "label": term["label"],
                "index": i,
                "context": [],
            }
            for i, val in enumerate(term["context"]):
                # NOTE: temporary fix for missing keys in context
                for key in ["source", "definition", "naderToegelicht", "wetcontext"]:
                    if key not in val:
                        val[key] = ""
                context_dict = {
                    "id": uuid.uuid4(),
                    "isSource": False,
                    "source": val["source"],
                    "definition": val["definition"],
                    "naderToegelicht": val["naderToegelicht"],
                    "wetcontext": {
                        "url": val["wetcontext"],
                    },
                }
                term_dict["context"].append(context_dict)
            taxonomy.append({"type": "taxonomy", "value": term_dict})
        return "taxonomy", taxonomy
    except Exception as e:
        logger.error(f"An error occurred while processing taxonomy data: {e}")
        return None


def process_selectielijst(data: dict) -> list[dict]:
    """Create output structure for selectielijsten"""
    try:
        grouped_data = defaultdict(lambda: {"name": "", "rows": [], "indices": []})

        for index, row in enumerate(data["selectielijsten"]):
            selectielijsten_name = row["selectielijsten"]
            new_row = row.copy()
            new_row["isSource"] = False

            grouped_data[selectielijsten_name]["name"] = selectielijsten_name
            grouped_data[selectielijsten_name]["rows"].append(new_row)
            grouped_data[selectielijsten_name]["indices"].append(index)

        selectielijsten_lst = []
        for source in list(grouped_data.values()):  # list of dicts
            selectielijsten_lst.append({"id": uuid.uuid4(), "type": "selectielijst", "value": source})
        return "selectielijsten", selectielijsten_lst
    except Exception as e:
        logger.error(f"An error occurred while processing selectielijst data: {e}")
        return None
