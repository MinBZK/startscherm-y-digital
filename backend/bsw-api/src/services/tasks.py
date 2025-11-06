from utils.logging.logger import logger
from elastic.elastic import ES, ES_INDEX


async def get_n_tasks(user_id, n=6) -> list[dict]:
    logger.info(f"Fetching {n} tasks for user {user_id}")

    try:
        es = ES

        query = {
            "size": 5,
            "query": {"match": {"user_id": user_id}},
        }

        print(f"Query: {query}")

        response = es.search(index="task-index", body=query)
        print(f"Response: {response}")
        print(f"Hits: {response['hits']['hits']}")
        print(f"Total hits: {response['hits']['total']['value']}")
        documents = [hit["_source"] for hit in response["hits"]["hits"]]
        print(f"Documents: {documents}")

        return documents
    except Exception as e:
        logger.error(f"Error fetching latest documents: {e}")
        return []


tasks = [
    {
        "id": "1",
        "title": "Verzamelen documenten en voorleggen",
        "dueDate": "2025-06-17T00:00:00Z",
        "status": "notStarted",
        "user_id": "953087ce-a143-41f6-b5a8-1d9318516bdc",
        "relatedTo": {
            "type": "channel",
            "title": "Woo-verzoek over verzoek documenten EU-inbraak",
            "url": "https://teams.microsoft.com/l/channel/example",
        },
    },
    {
        "id": "2",
        "title": "Controleren en beoordelen gelakte documenten",
        "dueDate": "2025-06-14T00:00:00Z",
        "user_id": "953087ce-a143-41f6-b5a8-1d9318516bdc",
        "status": "inProgress",
    },
    {
        "id": "3",
        "title": "Uitvoeren intake met aanvrager",
        "user_id": "953087ce-a143-41f6-b5a8-1d9318516bdc",
        "dueDate": "2025-06-18T00:00:00Z",
        "status": "notStarted",
    },
    {
        "id": "4",
        "title": "Controleren en beoordelen gelakte documenten",
        "dueDate": "2025-06-24T00:00:00Z",
        "user_id": "953087ce-a143-41f6-b5a8-1d9318516bdc",
        "status": "waitinOnOthers",
    },
    {
        "id": "5",
        "title": "In gang zetten parafeerlijn",
        "user_id": "953087ce-a143-41f6-b5a8-1d9318516bdc",
        "dueDate": None,
        "status": "completed",
    },
    {
        "id": "6",
        "title": "Uitvoeren intake met aanvrager",
        "user_id": "953087ce-a143-41f6-b5a8-1d9318516bdc",
        "dueDate": "2025-06-28T00:00:00Z",
        "status": "notStarted",
    },
    {
        "id": "7",
        "title": "Aafspraaken met aanvrager",
        "user_id": "953087ce-a143-41f6-b5a8-1d9318516bdc",
        "dueDate": "2025-06-28T00:00:00Z",
        "status": "notStarted",
    },
]


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
                    "must": [{"terms": {"lastmodified_user_id.keyword": [user_id]}}]
                }
            },
        }

        query = {
            "size": 5,
            "sort": [{"lastmodifiedtime": {"order": "desc"}}],
            "query": {"match_all": {}},
        }

        response = es.search(index=ES_INDEX, body=query)
        documents = [hit["_source"] for hit in response["hits"]["hits"]]
        documents_out = [
            {
                "name": doc.get("raw_title"),
                "filetype": doc.get("filetype"),
                "url": doc.get("url"),
                "linked_dossier": doc.get("dossier_name", ""),
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
