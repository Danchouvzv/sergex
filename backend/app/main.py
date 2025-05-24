from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.ws import telemetry_ws
from app.db.session import init_db
from app.core.mqtt_client import mqtt_client


app = FastAPI(
    title="Sergex Air UTM API",
    description="API for the Unmanned Traffic Management system",
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include the API router which contains all API endpoints
app.include_router(api_router, prefix="/api")

# Include WebSocket router
app.include_router(telemetry_ws.router)

@app.on_event("startup")
async def startup_event():
    """Initialize the database and start MQTT client on startup."""
    init_db()
    
    mqtt_client.connect()
    mqtt_client.start()

@app.on_event("shutdown")
async def shutdown_event():
    """Stop MQTT client on shutdown."""
    mqtt_client.stop()

@app.get("/", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "Sergex Air UTM API is running"} 