from elastic.elastic import ES, ES_INDEX
from utils.logging.logger import logger


def get_document_from_id(document_id: str) -> dict:
    pass


def get_documents() -> list[dict]:
    pass


async def get_latest_documents(user_id: str) -> list[dict]:
    try:
        es = ES

        query = {
            "size": 5,
            "sort": [{"lastmodifiedtime": {"order": "desc"}}],
            "query": {
                "bool": {
                    "must": [
                        {"terms": {"lastmodified_user_id.keyword": [user_id]}},
                        {"term": {"accessible_to_users.keyword": user_id}},
                    ]
                }
            },
        }

        # query = {
        #     "size": 5,
        #     "sort": [{"lastmodifiedtime": {"order": "desc"}}],
        #     "query": {"match_all": {}},
        # }

        response = es.search(index=ES_INDEX, body=query)
        documents = [hit["_source"] for hit in response["hits"]["hits"]]
        documents_out = [
            {
                "name": doc.get("raw_title"),
                "filetype": doc.get("filetype"),
                "url": doc.get("url"),
                "linked_dossier": doc.get("dossier_name", ""),
                "nextcloud_id": doc.get("nextcloud_id", ""),
            }
            for doc in documents
        ]
        return documents_out
    except Exception as e:
        logger.error(f"Error fetching latest documents: {e}")
        return []


# output_file = {"file_name": "output.txt", "filetype": Word, }


def open_document_link(document_id: str):  #  -> URL
    pass
