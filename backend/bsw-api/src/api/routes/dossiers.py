from utils.logging.logger import logger

from fastapi import APIRouter, Depends
from services.dossiers import (
    get_dossier_from_id,
    new_dossier,
    get_dossiers,
    get_latest_dossiers,
    update_dossier_opened_status,
)
from dependencies.auth import get_current_user_id

app = APIRouter(prefix="/api/dossiers", tags=["dossier"])


@app.post("/create")
async def create():
    return new_dossier()


@app.get("/dossier/{dossier_id}")
async def get_dossier(dossier_id: str, user_id: str = Depends(get_current_user_id)):
    return get_dossier_from_id(dossier_id, user_id)


@app.patch("/dossier/{dossier_id}/opened")
async def update_dossier_status(
    dossier_id: str, user_id: str = Depends(get_current_user_id)
):
    logger.info(f"Updating opened status for dossier {dossier_id} for user {user_id}")
    return update_dossier_opened_status(dossier_id, user_id)


@app.get("/get_latest")
async def get_latest(user_id: str = Depends(get_current_user_id)):
    logger.info(f"Fetching latest dossiers for user: {user_id}")
    return await get_latest_dossiers(user_id)


@app.get("/get_all")
async def get_all():
    return get_dossiers()
