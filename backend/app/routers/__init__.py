from .cows import router as cows_router
from .activity import router as activity_router
from .temperature import router as temperature_router
from .heart_rate import router as heart_rate_router

__all__ = ["cows_router", "activity_router", "temperature_router", "heart_rate_router"]
