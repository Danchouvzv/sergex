from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.drones import router as drones_router
from app.api.flights import router as flights_router
from app.api.no_fly_zones import router as no_fly_zones_router
from app.api.telemetry import router as telemetry_router
from app.api.violations import router as violations_router
from app.api.users import router as users_router
from app.api.admin import router as admin_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["authentication"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(drones_router, prefix="/drones", tags=["drones"])
api_router.include_router(flights_router, prefix="/flights", tags=["flights"])
api_router.include_router(no_fly_zones_router, prefix="/no-fly-zones", tags=["no-fly-zones"])
api_router.include_router(telemetry_router, prefix="/telemetry", tags=["telemetry"])
api_router.include_router(violations_router, prefix="/violations", tags=["violations"])
api_router.include_router(admin_router, prefix="/admin", tags=["admin"]) 