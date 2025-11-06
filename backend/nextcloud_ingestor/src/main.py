from __future__ import annotations

import os
import asyncio
import sys
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
import uvicorn
from config import Config
from ingestor import Ingestor

DRY_RUN = os.getenv('DRY_RUN', 'false').lower() == 'true'


app = FastAPI(
    title="NextCloud Ingestor API",
    description="API for running NextCloud to Elasticsearch ingestion",
    version="1.0.0"
)

# Global config and ingestor instance
config = Config.from_env(envfile='.env')


@app.get("/")
def root():
    return {"message": "NextCloud Ingestor is running"}


@app.post("/ingest/full")
async def run_full_ingest_endpoint(dry_run: bool = None):
    """Run full ingest (recreates indices). Traverses all files and reindexes everything."""
    try:
        # Use provided dry_run parameter or fall back to environment variable
        effective_dry_run = DRY_RUN if dry_run is None else dry_run
        
        ingestor = Ingestor(config)
        
        # Run in background task
        asyncio.create_task(ingestor.run_full_ingest(dry_run=effective_dry_run))
        
        return {
            "status": "Full ingestion started",
            "dry_run": effective_dry_run,
            "message": "Recreating indices and processing all files"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start full ingestion: {str(e)}")


async def run_full_ingest_direct(dry_run: bool = None):
    """Direct execution of full ingest for command line usage."""
    try:
        # Use provided dry_run parameter or fall back to environment variable
        effective_dry_run = DRY_RUN if dry_run is None else dry_run
        
        ingestor = Ingestor(config)
        
        # Run directly and await completion
        await ingestor.run_full_ingest(dry_run=effective_dry_run)
        
        print(f"Full ingestion completed successfully (dry_run={effective_dry_run})")
        
    except Exception as e:
        print(f"Failed to run full ingestion: {str(e)}")
        raise


@app.post("/ingest/incremental")
async def run_incremental_ingest_endpoint(dry_run: bool = Query(default=None, description="Override DRY_RUN environment variable")):
    """Run incremental ingest using Activity API. Processes only changed files since last run."""
    try:
        # Use provided dry_run parameter or fall back to environment variable
        effective_dry_run = DRY_RUN if dry_run is None else dry_run
        
        ingestor = Ingestor(config)
        
        # Run incremental ingest without fallback functionality (as requested)
        asyncio.create_task(ingestor.run_incremental_ingest(dry_run=effective_dry_run, fallback_to_full=False))
        
        return {
            "status": "Incremental ingestion started",
            "dry_run": effective_dry_run,
            "message": "Processing activities since last run"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start incremental ingestion: {str(e)}")


async def run_incremental_ingest_direct(dry_run: bool = None):
    """Direct execution of incremental ingest for command line usage."""
    try:
        # Use provided dry_run parameter or fall back to environment variable
        effective_dry_run = DRY_RUN if dry_run is None else dry_run
        
        ingestor = Ingestor(config)
        
        # Run directly and await completion
        await ingestor.run_incremental_ingest(dry_run=effective_dry_run, fallback_to_full=False)
        
        print(f"Incremental ingestion completed successfully (dry_run={effective_dry_run})")
        
    except Exception as e:
        print(f"Failed to run incremental ingestion: {str(e)}")
        raise


@app.get("/run")
async def run_ingestor(dry_run: bool = Query(default=None, description="Override DRY_RUN environment variable")):
    """Legacy endpoint - runs full ingest for backwards compatibility."""
    try:
        # Use provided dry_run parameter or fall back to environment variable
        effective_dry_run = DRY_RUN if dry_run is None else dry_run
        
        ingestor = Ingestor(config)
        asyncio.create_task(ingestor.run_full_ingest(dry_run=effective_dry_run))
        
        return {
            "status": "Running ingestion (full)",
            "dry_run": effective_dry_run,
            "message": "Using legacy endpoint - running full ingest"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start ingestion: {str(e)}")


if __name__ == "__main__":
    args = sys.argv[1:]  # skip file name
    if len(args) > 0 and args[0] == "api":
        # Start API server
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    elif len(args) > 0 and args[0] == "full":
        asyncio.run(run_full_ingest_direct())
    elif len(args) > 0 and args[0] == "incremental":
        asyncio.run(run_incremental_ingest_direct())
    else:
        print("Usage: python main.py [api|full|incremental]")
        print("  api         - Start the FastAPI server")
        print("  full        - Run full ingestion (recreates indices)")
        print("  incremental - Run incremental ingestion (processes changes since last run)")
        sys.exit(1)
