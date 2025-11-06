from fastapi import APIRouter, Depends
from services.tasks import get_n_tasks

# from src.models.document import DocumentOut
from dependencies.auth import get_current_user_id
from utils.logging.logger import logger

app = APIRouter(prefix="/api/tasks", tags=["Task"])


@app.get("/get_tasks")
async def get_current_tasks(user_id: str = Depends(get_current_user_id)):
    logger.info(f"Fetching tasks for user: {user_id}")
    return await get_n_tasks(user_id)
