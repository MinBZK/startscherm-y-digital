from utils.logging.logger import logger

from fastapi import APIRouter, Depends
from services.calendar import get_week_events

# from src.models.document import DocumentOut
from dependencies.auth import get_current_user_id

app = APIRouter(prefix="/api/calendar", tags=["Calendar"])


@app.get("/get_week_events")
async def get_current_week_events(user_id: str = Depends(get_current_user_id)):
    logger.info(f"Fetching events for current week for user: {user_id}")
    return await get_week_events(user_id)
