from elastic.elastic import ES
from utils.logging.logger import logger
import random


def get_dossier_from_id(dossier_id: str, user_id: str) -> dict:
    es = ES
    try:
        response = es.get(index="dossier-index", id=dossier_id)
        dossier = response["_source"]
        if user_id not in dossier.get("members", []):
            logger.warning(f"User {user_id} is not a member of dossier {dossier_id}")
            return {}
        logger.debug(f"Fetched dossier: {dossier}")
        return dossier
    except Exception as e:
        logger.error(f"Error fetching dossier with ID {dossier_id}: {e}")
        return {}


def new_dossier() -> None:
    pass


def get_dossiers() -> list[dict]:
    """Get all dossiers - currently not implemented with user filtering."""
    try:
        es = ES
        
        query = {
            "size": 100,  # Limit to prevent large responses
            "sort": [
                {"created_datetime": {"order": "desc", "missing": "_last"}}
            ],
            "query": {"match_all": {}}
        }
        
        response = es.search(index="dossier-index", body=query)
        dossiers = [hit["_source"] for hit in response["hits"]["hits"]]
        
        logger.debug(f"Fetched {len(dossiers)} dossiers")
        return dossiers
    except Exception as e:
        logger.error(f"Error fetching all dossiers: {e}")
        return []


async def get_latest_dossiers(user_id: str) -> list[dict]:
    try:
        es = ES

        query = {
            "size": 5,
            "sort": [
                {"lastmodified_datetime": {"order": "desc", "missing": "_last"}},
                {"created_datetime": {"order": "desc", "missing": "_last"}}
            ],
            "query": {"bool": {"must": [{"terms": {"members": [user_id]}}]}},
        }

        response = es.search(index="dossier-index", body=query)
        dossiers = [hit["_source"] for hit in response["hits"]["hits"]]

        logger.debug(f"Fetched {len(dossiers)} dossiers for user {user_id}")
        dossiers_out = [
            {
                "name": dossier.get("dossier_name"),
                "url": dossier.get("webURL"),
                "file_id": dossier.get("file_id"),  # Include Nextcloud file ID
                "progress": random.randint(
                    0, 100
                ),  # TODO: implement real progress tracking
                "linked_zaak": "",
                "last_modified": dossier.get("lastmodified_datetime") or dossier.get("created_datetime"),
                "is_unopened": dossier.get("unopened"),
                "dossier_id": dossier.get("dossier_id"),
                "date_received": dossier.get("created_datetime"),
            }
            for dossier in dossiers
        ]
        return dossiers_out
    except Exception as e:
        logger.error(f"Error fetching latest dossiers: {e}")
        return []


def update_dossier_opened_status(dossier_id: str, user_id: str):
    logger.info(f"Opening new dossier {dossier_id} and updating status")
    es = ES
    try:
        response = es.get(index="dossier-index", id=dossier_id)
        dossier = response["_source"]
        if user_id not in dossier.get("members", []):
            logger.warning(f"User {user_id} is not a member of dossier {dossier_id}")
            return
        es.update(
            index="dossier-index", id=dossier_id, body={"doc": {"unopened": False}}
        )
        logger.info(f"Dossier {dossier_id} status updated to opened")
    except Exception as e:
        logger.error(f"Error updating dossier {dossier_id} status: {e}")
