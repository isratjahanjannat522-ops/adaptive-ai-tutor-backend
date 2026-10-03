from fastapi import APIRouter
from app.api.auth_routes import router as auth_router
from app.api.student_model_routes import router as student_model_router
from app.api.lesson_routes import router as lesson_router
from app.api.quiz_routes import router as quiz_router
from app.api.progress_routes import router as progress_router
from app.api.admin_routes import router as admin_router
from app.api.evaluation_routes import router as evaluation_router
from app.api.chat_routes import router as chat_router
from app.api.exercise_routes import router as exercise_router
from app.api.goals_routes import router as goals_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(student_model_router)
api_router.include_router(lesson_router)
api_router.include_router(quiz_router)
api_router.include_router(progress_router)
api_router.include_router(admin_router)
api_router.include_router(evaluation_router)
api_router.include_router(chat_router)
api_router.include_router(exercise_router)
api_router.include_router(goals_router)
