from elastic.elastic import ES
from utils.logging.logger import logger
from typing import Dict, List, Optional


def create_dossier_service():
    """
    Create a dossier with the given name and description for the user.
    Also creates 5 example documents in bsw-index and 5 example tasks in task-index.
    Returns a dictionary with the status of the operation.
    """

    dossier_name = "Klachtschrift_202507"
    user_id = "Gerwen"
    logger.info(f"Creating dossier: {dossier_name}")
    description = "Klachtschrift"
    es = ES
    try:
        # Create 5 documents in bsw-index
        for i in range(5):
            doc = ex_doc.copy()
            doc["title"] = f"{ex_doc['title']}_{i+1}"
            doc["dossier_name"] = dossier_name
            doc["author_id"] = user_id
            doc["description"] = description
            es.index(index="bsw-index", body=doc)
        # Create 5 tasks in task-index
        for i in range(5):
            task = ex_task.copy()
            task["id"] = str(i + 1)
            task["title"] = f"{ex_task['title']} #{i+1}"
            task["relatedTo"]["title"] = dossier_name
            es.index(index="task-index", body=task)
        return {
            "status": "success",
            "message": f"Dossier '{dossier_name}' created successfully",
            "dossier_name": dossier_name,
            "description": description,
        }
    except Exception as e:
        logger.error(f"Error creating dossier and related docs/tasks: {e}")
        return {
            "status": "error",
            "message": str(e),
            "dossier_name": dossier_name,
            "description": description,
        }


ex_task = {
    "id": "1",
    "title": "Verzamelen documenten en voorleggen",
    "dueDate": "2025-06-17T00:00:00Z",
    "status": "notStarted",
    "relatedTo": {
        "type": "channel",
        "title": "Woo-verzoek over verzoek documenten EU-inbraak",
        "url": "https://teams.microsoft.com/l/channel/example",
    },
}


ex_doc = {
    "title": "Presentation_Test_BSW",
    "raw_title": "Presentation_Test_BSW.pptx",
    "url": "https://ydigital.sharepoint.com/sites/ProefopstelingBSW/_layouts/15/Doc.aspx?sourcedoc=%7B396FB14C-4242-4CED-8208-9FB3DC75E4B0%7D&file=Presentation_Test_BSW.pptx&action=edit&mobileredirect=true",
    "datetime_published": "2025-06-26T09:01:11.210748",
    "created_date": "2025-05-08T13:23:03Z",
    "lastmodifiedtime": "2025-05-13T09:44:38Z",
    "sharepoint_id": "01HUKLPX2MWFXTSQSC5VGIECE7WPOHLZFQ",
    "drive_id": "b!ocT3bGO4SUCQA4OstGbBOXThL1VZ93RHobckKy6khGplE8YdKJSeQpjRR7SrAMWb",
    "author": "Anna Dollbo",
    "author_id": "c5c70443-e0b5-4123-8c79-121a92a9e75f",
    "lastmodified_user_id": "c5c70443-e0b5-4123-8c79-121a92a9e75f",
    "size": "37.8 kB",
    "author_modified": "Anna Dollbo",
    "filepath": "Documents/General",
    "filetype": "Powerpoint",
    "needs_download": "not",
    "full_text": "\n\nThis test BSW \njenfklremlfknerkfnlrenflre\n\nBla bla bal\nNklenflwelk\n\nThis is a test text to see if this can be parsed. Lets see!\n\n/docProps/thumbnail.jpeg\n\n",
    "paragraphs": [
        {"id": 0, "text": "This test BSW jenfklremlfknerkfnlrenflre"},
        {"id": 1, "text": "Bla bla bal Nklenflwelk"},
        {
            "id": 2,
            "text": "This is a test text to see if this can be parsed. Lets see!",
        },
        {"id": 3, "text": "/docProps/thumbnail.jpeg"},
    ],
    "accessible_to_users": [
        "47b1d9b9-dfc8-4fb0-8d77-b762cbde22a9",
        "5d006320-e471-4013-b34b-312026fb5e9e",
        "28235788-ad54-4633-a62c-2fbe00c3e707",
        "4b79227a-dd32-48ca-a7a2-94dea10fab5b",
        "c5c70443-e0b5-4123-8c79-121a92a9e75f",
    ],
    "topics": [],
    "number_pages": "2",
}


def get_query(keyword: str, filters: Optional[Dict[str, List[str]]] = None):
    # Base query with keyword search

    logger.info(f"Creating query for keyword: {keyword} with filters: {filters}")
    query = {
        "query": {"bool": {"must": [{"match": {"full_text": keyword}}], "filter": []}},
        "aggs": {
            "agg-author": {"terms": {"field": "author.keyword"}},
            "agg-datetime_published": {"terms": {"field": "datetime_published"}},
            "agg-filetype": {"terms": {"field": "filetype.keyword"}},
            "agg-created_date": {"terms": {"field": "created_date"}},
            "agg-dossier_name": {"terms": {"field": "dossier_name.keyword"}},
        },
    }

    # Add filters if provided

    for field, values in filters.items():
        logger.info(f"Adding filter for field: {field} with values: {values}")
        if values:  # Only add filter if values are provided
            field_mapping = {
                "agg-author": "author",
                "agg-datetime_published": "datetime_published",
                "agg-filetype": "filetype",
                "agg-created_date": "created_date",
                "agg-dossier_name": "dossier_name",
            }
            if field in field_mapping:
                query["query"]["bool"]["must"].append(
                    {"match": {field_mapping[field]: values}}
                )

    logger.info(f"Created query: {query}")

    return query


def search_keywords(
    query: str, user_id: str, filters: Optional[Dict[str, List[str]]] = None
) -> dict:
    es = ES
    try:

        logger.info(f"Searching for query: {get_query(query, filters)}")
        response = es.search(
            index="bsw-index", body=get_query(query, filters), size=1000
        )
        hits = response.get("hits", {}).get("hits", [])
        aggs = response.get("aggregations", {})
        logger.info(
            f"Performed search query: {query} "
            f"with filters: {filters} for user: {user_id}"
        )

        result = {
            "results": response.get("hits", {}).get("total", {}).get("value", 0),
            "hits": hits,
            "aggregations": aggs,
        }
        return result
    except Exception as e:
        logger.error(f"Error searching: {e}")
        return {}
