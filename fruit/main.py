import os

from fastapi import FastAPI
from fruit.api.fruit_api import router as fruit_router
from fruit.api.location_api import router as location_router


# Imports a pre-defined set of routes (an APIRouter instance) from a separate file located at fruit/api/fruit_api.py. The as fruit_router part renames it locally within this file to make its purpose clear.

app = FastAPI()

# • app.include_router(...): This method tells your main application to register and activate all the individual endpoints (like GET, POST, etc.) defined inside fruit_router.
# • Instead of cluttering this main file with dozens of specific route functions (e.g., fetching a list of fruits or adding a new fruit), you hook them all up at once using this single line.
app.include_router(fruit_router)
app.include_router(location_router)


# General health check at the VM level after Load balancer
@app.get("/healthz")
def healthz():
    return {"status": "ok"}


# Test route for Cloud Run    
@app.get("/health")
def health():
    return {"status": "ok", "version": os.getenv("APP_VERSION", "v1")}