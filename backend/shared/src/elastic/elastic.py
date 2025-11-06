from elasticsearch import Elasticsearch
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logging.logger import logger
import os

ES_INDEX = "bsw-index"


def get_elasticsearch():
    """Get ElasticSearch client based on the config details

    :return: ElasticSearch client
    """
    logger.info("Creating ElasticSearch client...")
    
    # Get Elasticsearch hostname from environment variable
    es_hostname = os.getenv("ES_HOSTNAME", "http://bsw-elasticsearch:9200")
    
    es = Elasticsearch(
        hosts=[es_hostname],
        http_compress=True,
        retry_on_timeout=True,
        request_timeout=30,
        verify_certs=False,
    )

    logger.info(f"ElasticSearch connection made: {es.ping()}")

    if not es.ping():
        logger.info("ElasticSearch connection failed!")

    return es


# Global variable to store the ES client
_ES_CLIENT = None

def get_es_client():
    """Get Elasticsearch client lazily"""
    global _ES_CLIENT
    if _ES_CLIENT is None:
        logger.info("Initializing ElasticSearch client...")
        _ES_CLIENT = get_elasticsearch()
    return _ES_CLIENT

# For backward compatibility, expose ES as a property
class ESProxy:
    def __getattr__(self, name):
        return getattr(get_es_client(), name)

ES = ESProxy()