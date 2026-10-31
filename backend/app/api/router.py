from fastapi import APIRouter

from ..admin.router import router as admin_router
from ..auth.router import router as auth_router
from ..composition.router import router as composition_router
from .attempts import router as attempts_router
from .engine import router as engine_router
from .lessons import router as lessons_router
from .learning import router as learning_router
from .music import router as music_router
from .practice import router as practice_router
from .review import router as review_router

api_router = APIRouter()
api_router.include_router(engine_router)
api_router.include_router(lessons_router)
api_router.include_router(learning_router)
api_router.include_router(attempts_router)
api_router.include_router(review_router)
api_router.include_router(music_router)
api_router.include_router(practice_router)
api_router.include_router(composition_router)
api_router.include_router(auth_router)
api_router.include_router(admin_router)
