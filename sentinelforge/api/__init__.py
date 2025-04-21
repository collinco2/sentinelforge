# This file makes the 'api' directory a Python package.

from fastapi import FastAPI

# Import routers from submodule files
# from .taxii import app as taxii_app # Keep commented unless merging apps
from .export import router as export_router

# Create the main FastAPI instance for the /api path (if mounted)
# Or potentially this could be the single main app for the whole project
# depending on desired structure.
app = FastAPI(title="SentinelForge API")

# Include routers from submodules
# app.include_router(taxii_app, prefix="/taxii", tags=["TAXII2-like"]) # Example if mounting taxii here
app.include_router(export_router)  # Mounted at /export (prefix defined in export.py)


# Example placeholder root endpoint for the API module
@app.get("/")
def read_root():
    return {"message": "Welcome to the SentinelForge API"}
