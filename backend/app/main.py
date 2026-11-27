from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import engine, Base
from .routers import cows_router, activity_router, temperature_router, heart_rate_router, gps_router
from . import models  # Ensures all ORM models are registered with Base.metadata

# Auto-create SQLite database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Central cloud telemetry backend for AI-powered cow collar: "
                "12-feature activity classification, CUSUM temperature anomaly detection, "
                "heart rate monitoring, and GPS polygon geofencing."
)

# CORS Middleware (allows web dashboard / mobile app integration)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(cows_router, prefix=settings.API_V1_STR)
app.include_router(activity_router, prefix=settings.API_V1_STR)
app.include_router(temperature_router, prefix=settings.API_V1_STR)
app.include_router(heart_rate_router, prefix=settings.API_V1_STR)
app.include_router(gps_router, prefix=settings.API_V1_STR)

@app.get("/", tags=["System Health"])
def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "HEALTHY",
        "docs_url": "/docs",
        "endpoints": {
            "cows": f"{settings.API_V1_STR}/cows",
            "activity_telemetry": f"{settings.API_V1_STR}/activity/telemetry",
            "activity_time_budget": f"{settings.API_V1_STR}/activity/cow/{{tag_id}}/time-budget",
            "activity_evaluate_anomalies": f"{settings.API_V1_STR}/activity/cow/{{tag_id}}/evaluate-anomalies",
            "temperature_telemetry": f"{settings.API_V1_STR}/temperature/telemetry",
            "temperature_baseline": f"{settings.API_V1_STR}/temperature/cow/{{tag_id}}/baseline",
            "temperature_alerts": f"{settings.API_V1_STR}/temperature/cow/{{tag_id}}/alerts",
            "heart_rate_telemetry": f"{settings.API_V1_STR}/heart-rate/telemetry",
            "heart_rate_baseline": f"{settings.API_V1_STR}/heart-rate/cow/{{tag_id}}/baseline",
            "heart_rate_alerts": f"{settings.API_V1_STR}/heart-rate/cow/{{tag_id}}/alerts",
            "gps_telemetry": f"{settings.API_V1_STR}/gps/telemetry",
            "gps_records": f"{settings.API_V1_STR}/gps/cow/{{tag_id}}/records",
            "gps_alerts": f"{settings.API_V1_STR}/gps/cow/{{tag_id}}/alerts",
            "gps_farm_polygon": f"{settings.API_V1_STR}/gps/farm-polygon",
        }
    }
