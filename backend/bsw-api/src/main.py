import os
import logging
import uvicorn
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

import sys
import os
sys.path.insert(0, '/home/bsw/shared')
from utils.logging.logger import logger
from api.models import ChatQuery
from ir.db.database import get_db
from api_utils.clients.httpx_client import get_http_client
from api.routes.wegwijs_in_regels_search import app as system_router
from api.routes.documents import app as documents_router
from api.routes.dossiers import app as dossiers_router
from api.routes.calendar import app as calendar_router
from api.routes.tasks import app as task_router
from api.routes.search import app as search_router
from ir.search.pipeline_runner import run_pipeline
from services.search import create_dossier_service
from generation.interface import get_answer_llm


import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="stopwordsiso._core")


app = FastAPI(
    title="API",
    description="Beter Samenwerken API",
    version="1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system_router)
app.include_router(documents_router)
app.include_router(dossiers_router)
app.include_router(calendar_router)
app.include_router(task_router)
app.include_router(search_router)


@app.middleware("http")
async def middleware(request: Request, call_next):
    body = await request.body() if hasattr(request, 'body') else ""

    response = await call_next(request)
    
    # Only log detailed info for errors or when explicitly enabled
    debug_requests = os.getenv("DEBUG_REQUESTS", "false").lower() == "true"
    is_error = response.status_code >= 400
    
    if is_error:
        # Always log errors with full details
        logger.error(f"Error {response.status_code}: {request.method} {request.url}")
        logger.error(f"Request headers: {request.headers}")
        logger.error(f"Request query params: {request.query_params}")
        logger.error(f"Request client: {request.client}")
    elif debug_requests:
        # Log full details only when debug is explicitly enabled
        logger.info(f"Request: {request.method} {request.url} -> {response.status_code}")
        logger.info(f"Request headers: {request.headers}")
        logger.info(f"Request body: {body}")
        logger.info(f"Request query params: {request.query_params}")
        logger.info(f"Request client: {request.client}")
    else:
        # Log only basic info for successful API requests
        if str(request.url.path).startswith(("/api/", "/chat")):
            logger.debug(f"{request.method} {request.url.path} -> {response.status_code}")
    
    return response


@app.post("/chat")
async def query_pipeline(
    chat_query: ChatQuery,
    db: Session = Depends(get_db),
    http_client=Depends(get_http_client),
):
    """Query pipeline"""

    logger.info(f"Received query: {chat_query.message}")
    result = await run_pipeline(chat_query=chat_query, db=db, http_client=http_client)

    return {"message": result["response"]}


@app.post("/chat-llm")
async def chat_llm(chat_query: ChatQuery):
    """Chat with LLM only"""
    logger.info(f"Received LLM chat query: {chat_query.message}")
    response = await get_answer_llm(chat_query.message, None)
    response = response.content if hasattr(response, "content") else str(response)
    return {"message": response}


# NOTE: output not compatible with frontend yet
@app.post("/api/pipeline")
async def query_pipeline_data(
    chat_query: ChatQuery,
    db: Session = Depends(get_db),
    http_client=Depends(get_http_client),
):
    """Query pipeline"""
    logger.info(f"Received query: {chat_query.message}")
    dossier_id = chat_query.dossier.dossier_id if chat_query.dossier else None
    result = await run_pipeline(
        chat_query=chat_query, db=db, http_client=http_client, dossier_id=dossier_id
    )
    return result


@app.get("/api/create_dossier")
async def create_dossier():
    print(f"Creating dossier")
    result = await create_dossier_service()


if __name__ == "__main__":
    logger.info("Starting API server...")
    
    # Configure uvicorn logging
    log_level = os.getenv("LOG_LEVEL", "INFO").lower()
    access_log = os.getenv("ACCESS_LOG", "false").lower() == "true"
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5000,
        reload=False,
        log_level=log_level,
        access_log=access_log,  # Disable uvicorn's default access logging
    )
