import logging
import hashlib
import sys


# --------------------- Utilities ---------------------
logger = logging.getLogger("nextcloud_ingestor")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

SUPPORTED_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".ppt", ".pptx",
    ".xls", ".xlsx", ".txt", ".md"
}


def hash(data: str) -> str:
    h = hashlib.sha256()
    h.update(data.encode("utf-8"))
    return h.hexdigest()
