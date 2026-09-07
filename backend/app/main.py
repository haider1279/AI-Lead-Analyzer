from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from .utils.config import settings
from .routes import (
    auth,
    teams,
    leads,
    activities,
    tasks,
    ai,
    proposals,
    dashboard,
    reports,
    settings as settings_router,
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Euroshub Lead Management (Sales Hub) API Backend"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Friendly Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    error_msgs = []
    for err in errors:
        loc = " -> ".join([str(l) for l in err.get("loc", []) if l != "body"])
        msg = err.get("msg", "Invalid input")
        error_msgs.append(f"{loc}: {msg}" if loc else msg)
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "message": "; ".join(error_msgs) or "The submitted data is invalid. Please check your inputs.",
            "details": errors
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"[SERVER ERROR] {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Server Error",
            "message": "An unexpected error occurred while processing your request. Please try again later."
        }
    )

# Include Routers
app.include_router(auth.router)
app.include_router(teams.router)
app.include_router(leads.router)
app.include_router(activities.router)
app.include_router(tasks.router)
app.include_router(ai.router)
app.include_router(proposals.router)
app.include_router(dashboard.router)
app.include_router(reports.router)
app.include_router(settings_router.router)

@app.get("/health", tags=["System"])
@app.get("/", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }
