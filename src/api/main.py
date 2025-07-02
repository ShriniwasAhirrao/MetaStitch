from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.background import BackgroundTasks
import logging

from config.settings import settings
from config.logging_config import setup_logging

from src.api.routes.upload import router as upload_router
from src.api.routes.process import router as process_router
from src.api.routes.status import router as status_router
from src.api.routes.results import router as results_router

from src.api.middleware.auth_middleware import AuthMiddleware
from src.api.middleware.error_handler import ErrorHandlerMiddleware
from src.api.middleware.logging_middleware import LoggingMiddleware

from src.agents.text_extractor.text_extractor_agent import TextExtractorAgent
from src.pipelines.pipeline_orchestrator import PipelineOrchestrator

app = FastAPI(
    title="Unstructured Data Integration Agent API",
    description="API for processing and extracting data from unstructured documents",
    version="1.0.0"
)

# Setup logging
setup_logging()

# Initialize agents and pipelines
text_extractor_agent = TextExtractorAgent()
pipeline_orchestrator = PipelineOrchestrator()

# Dependency injection example (can be expanded as needed)
def get_text_extractor_agent():
    return text_extractor_agent

def get_pipeline_orchestrator():
    return pipeline_orchestrator

# Include routers with dependencies
app.include_router(
    upload_router,
    prefix="/upload",
    tags=["upload"],
    dependencies=[],
)

app.include_router(
    process_router,
    prefix="/process",
    tags=["process"],
    dependencies=[],
)

app.include_router(
    status_router,
    prefix="/status",
    tags=["status"],
    dependencies=[],
)

app.include_router(
    results_router,
    prefix="/results",
    tags=["results"],
    dependencies=[],
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted hosts middleware if configured
if settings.trusted_hosts:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.trusted_hosts,
    )

# Add custom middleware
app.add_middleware(AuthMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(ErrorHandlerMiddleware)

# Root endpoint for health check
@app.get("/", tags=["health"])
async def root():
    return {"status": "ok", "message": "Unstructured Data Integration Agent API is running."}

# Example background task usage for long-running jobs
@app.post("/upload/file", tags=["upload"])
async def upload_file(background_tasks: BackgroundTasks, file: bytes = None):
    # Placeholder for file upload handling
    # Add background task for processing
    background_tasks.add_task(process_file_task, file)
    return {"message": "File upload received, processing started."}

async def process_file_task(file: bytes):
    # Placeholder for file processing logic
    # Use agents/pipelines here
    pass

# Explanation:
# This main.py sets up the FastAPI app with metadata and includes routers for upload, process, status, and results endpoints.
# CORS and trusted hosts middleware are configured for security and cross-origin support.
# Custom middleware for authentication, logging, and error handling are added to ensure robust API behavior.
# Dependency injection functions provide agents and pipelines to routers as needed.
# Background tasks are supported for long-running operations like file processing.
# The modular structure aligns with the project organization, keeping API routes, middleware, agents, and pipelines separate for maintainability.
