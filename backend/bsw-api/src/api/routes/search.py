import logging

from fastapi import APIRouter, Depends, Request
from services.search import search_keywords as search_keywords_service
from dependencies.auth import get_current_user_id

logger = logging.getLogger(__name__)
app = APIRouter(prefix="/api", tags=["search"])


@app.post("/search")
async def search_keywords(request: Request, user_id: str = Depends(get_current_user_id)):
    print(f"Received search query: for user: {user_id}")
    user_query = await request.json()
    logger.info(f"User query: {user_query} for user: {user_id}")
    return search_keywords_service(
        query=user_query.get("query", ""),
        filters=user_query.get("filters", {}),
        user_id=user_id,
    )
