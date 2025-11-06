import os
import io
import contextlib
from tika import parser as tika_parser  # type: ignore
from utils import logger
import dotenv

SUPPORTED_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".ppt", ".pptx",
    ".xls", ".xlsx", ".txt", ".md"
}

class NotSupportedError(Exception):
    """Custom exception for unsupported file types."""
    pass


dotenv.load_dotenv()
# Set Tika server endpoint from environment variable, default to localhost
os.environ['TIKA_SERVER_URL'] = dotenv.get_key(dotenv.find_dotenv(), 'TIKA_SERVER_URL') or 'http://localhost:9998'


class ContentExtractor:
    def __init__(self):
        self.tika_available = "tika_parser" in globals()
        self.tika_server_url = os.environ['TIKA_SERVER_URL']


    def can_extract(self, ext: str) -> bool:
        return ext.lower() in SUPPORTED_EXTENSIONS

    def extract(self, path: str, content: bytes) -> str:
        ext = os.path.splitext(path)[1].lower()
        if not self.can_extract(ext):
            logger.warning(f"Unsupported file extension for extraction: {ext}")
            raise NotSupportedError(f"Unsupported file extension: {ext}")
        # Prefer Tika for broad coverage, if available
        if self.tika_available:
            with contextlib.suppress(Exception):
                parsed = tika_parser.from_buffer(content, f"{self.tika_server_url}/tika")
                text = parsed.get("content")
                if text:
                    return text.strip()
        # Fallbacks per type
        if ext == ".pdf" and "fitz":
            import fitz
            return self._extract_pdf(content)
        if ext == ".txt" or ext == ".md":
            print("Extracting as \".txt\" or \".md\"")
            return self._extract_txt(content)
        return ""

    @staticmethod
    def _extract_txt(content: bytes) -> str:
        return content.decode("utf-8", errors="replace")

    @staticmethod
    def _extract_pdf(content: bytes) -> str:
        bio = io.BytesIO(content)
        doc = fitz.open(stream=bio, filetype="pdf")
        texts = []
        for page in doc:
            texts.append(page.get_text())
        return "\n".join(texts)
