from utils.logging.logger import logger

from fastapi import APIRouter, Depends
from services.documents import get_latest_documents

# from src.models.document import DocumentOut
from dependencies.auth import get_current_user_id

app = APIRouter(prefix="/api/documents", tags=["Documents"])


@app.get("/latest")
async def list_documents(user_id: str = Depends(get_current_user_id)):
    logger.info(f"Fetching latest documents for user: {user_id}")
    return await get_latest_documents(user_id)
