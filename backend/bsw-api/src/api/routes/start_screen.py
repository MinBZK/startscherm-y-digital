from pydantic import BaseModel

from fastapi import APIRouter, Depends
from starlette.middleware.sessions import SessionMiddleware

from utils.logging.logger import logger
from services.start_screen import get_start_screen_data
from dependencies.auth import get_current_user_id
from api.models.schemas.start_screen import StartScreenResponse
from api.models.schemas.shared import LinkResponse

app = APIRouter(tags=["dossier"])


app.add_middleware(
    SessionMiddleware, secret_key="your-secret", session_cookie="gov_session"
)


@app.get("/", response_model=StartScreenResponse)
async def get_start_screen(user_id: str = Depends(get_current_user_id)):
    return get_start_screen_data()


@app.get("/my_day")
async def get_my_day() -> LinkResponse:
    return


@app.get("/my_dossiers")
async def get_my_dossiers() -> LinkResponse:
    return


@app.get("/my_tasks")
async def get_my_tasks() -> LinkResponse:
    return


@app.get("/my_agenda")
async def get_my_agenda() -> LinkResponse:
    return


@app.get("/notifications")
async def get_my_notifications() -> LinkResponse:
    return
