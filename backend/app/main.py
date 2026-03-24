"""Main application entry point."""

import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import aiofiles
from celery.result import AsyncResult
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlmodel import Session

from app import crud
from app.celery_app import celery_app
from app.celery_schemas import (
    DataProcessRequest,
    EmailTaskRequest,
    TaskRevokeRequest,
    TaskRevokeResponse,
    TaskStatusResponse,
    TaskSubmitRequest,
    TaskSubmitResponse,
)
from app.converter_schemas import (
    ConversionResponse,
    ConversionStatusResponse,
    ConversionType,
    SupportedFormatsResponse,
)
from app.converter_service import UPLOAD_DIR, OUTPUT_DIR, convert_file, ConversionError
from app.converter_tasks import convert_document
from app.database import get_db, init_db
from app.models import (
    PostCreate,
    PostResponse,
    PostUpdate,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from app.settings import get_settings
from app.tasks import (
    example_task,
    process_data_task,
    send_email_task,
)

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Initialize database tables on startup
    init_db()
    yield


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="A Python API built with Better Fullstack",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to converter!"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


# Celery task endpoints
@app.post("/tasks/submit", response_model=TaskSubmitResponse)
async def submit_task(request: TaskSubmitRequest):
    """Submit a background task for processing.

    Returns immediately with a task ID that can be used
    to check the task status.
    """
    result = example_task.delay(request.message)
    return TaskSubmitResponse(
        task_id=result.id,
        status="PENDING",
    )


@app.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """Get the status of a submitted task.

    Returns the current status and result if completed.
    """
    result = AsyncResult(task_id, app=celery_app)

    response = TaskStatusResponse(
        task_id=task_id,
        status=result.status,
    )

    if result.ready():
        if result.successful():
            response.result = result.result
        else:
            response.error = str(result.result)
    elif result.status == "PROCESSING":
        # Get progress info from task meta
        meta = result.info
        if meta and isinstance(meta, dict):
            response.progress = meta.get("progress")

    return response


@app.post("/tasks/{task_id}/revoke", response_model=TaskRevokeResponse)
async def revoke_task(task_id: str, request: TaskRevokeRequest):
    """Revoke a pending or running task.

    If terminate is True, the task will be terminated even
    if it's currently running.
    """
    celery_app.control.revoke(task_id, terminate=request.terminate)
    return TaskRevokeResponse(
        task_id=task_id,
        revoked=True,
    )


@app.post("/tasks/email", response_model=TaskSubmitResponse)
async def submit_email_task(request: EmailTaskRequest):
    """Submit an email sending task.

    The email will be sent asynchronously in the background.
    """
    result = send_email_task.delay(
        to_email=request.to_email,
        subject=request.subject,
        body=request.body,
    )
    return TaskSubmitResponse(
        task_id=result.id,
        status="PENDING",
    )


@app.post("/tasks/process-data", response_model=TaskSubmitResponse)
async def submit_data_processing_task(request: DataProcessRequest):
    """Submit a data processing task.

    The data will be processed asynchronously. Check task
    status for progress updates.
    """
    result = process_data_task.delay(
        data=request.data,
        operation=request.operation or "default",
    )
    return TaskSubmitResponse(
        task_id=result.id,
        status="PENDING",
    )


# User endpoints
@app.post("/users", response_model=UserResponse, status_code=201)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user."""
    existing = crud.get_user_by_email(db, user.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db, user)


@app.get("/users", response_model=list[UserResponse])
async def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all users."""
    return crud.get_users(db, skip=skip, limit=limit)


@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get a user by ID."""
    user = crud.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):
    """Update a user."""
    updated = crud.update_user(db, user_id, user)
    if updated is None:
        raise HTTPException(status_code=404, detail="User not found")
    return updated


@app.delete("/users/{user_id}", status_code=204)
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Delete a user."""
    if not crud.delete_user(db, user_id):
        raise HTTPException(status_code=404, detail="User not found")


# Post endpoints
@app.post("/posts", response_model=PostResponse, status_code=201)
async def create_post(post: PostCreate, db: Session = Depends(get_db)):
    """Create a new post."""
    # Verify author exists
    if crud.get_user(db, post.author_id) is None:
        raise HTTPException(status_code=400, detail="Author not found")
    return crud.create_post(db, post)


@app.get("/posts", response_model=list[PostResponse])
async def list_posts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all posts."""
    return crud.get_posts(db, skip=skip, limit=limit)


@app.get("/posts/{post_id}", response_model=PostResponse)
async def get_post(post_id: int, db: Session = Depends(get_db)):
    """Get a post by ID."""
    post = crud.get_post(db, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@app.patch("/posts/{post_id}", response_model=PostResponse)
async def update_post(post_id: int, post: PostUpdate, db: Session = Depends(get_db)):
    """Update a post."""
    updated = crud.update_post(db, post_id, post)
    if updated is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return updated


@app.delete("/posts/{post_id}", status_code=204)
async def delete_post(post_id: int, db: Session = Depends(get_db)):
    """Delete a post."""
    if not crud.delete_post(db, post_id):
        raise HTTPException(status_code=404, detail="Post not found")


# Document Conversion endpoints
@app.get("/convert/formats", response_model=SupportedFormatsResponse)
async def get_supported_formats():
    """Get list of supported conversion formats."""
    return SupportedFormatsResponse(
        conversions=[
            {
                "type": ConversionType.PDF_TO_WORD.value,
                "from": "PDF (.pdf)",
                "to": "Word (.docx)",
                "description": "Convert PDF documents to editable Word format",
            },
            {
                "type": ConversionType.WORD_TO_PDF.value,
                "from": "Word (.docx, .doc)",
                "to": "PDF (.pdf)",
                "description": "Convert Word documents to PDF format (requires LibreOffice)",
            },
            {
                "type": ConversionType.WORD_TO_EXCEL.value,
                "from": "Word (.docx, .doc)",
                "to": "Excel (.xlsx)",
                "description": "Extract tables from Word documents to Excel spreadsheets",
            },
            {
                "type": ConversionType.EXCEL_TO_WORD.value,
                "from": "Excel (.xlsx, .xls)",
                "to": "Word (.docx)",
                "description": "Convert Excel spreadsheets to Word documents with tables",
            },
        ]
    )


@app.post("/convert/upload", response_model=ConversionResponse)
async def upload_and_convert(
    file: UploadFile = File(..., description="File to convert"),
    conversion_type: ConversionType = Form(..., description="Type of conversion"),
):
    """Upload a file and start conversion in the background.

    Returns a task ID that can be used to check conversion status.
    """
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # Generate unique filename to avoid collisions
    file_ext = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    upload_path = UPLOAD_DIR / unique_filename

    # Save uploaded file
    try:
        async with aiofiles.open(upload_path, "wb") as f:
            content = await file.read()
            await f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    # Submit conversion task
    result = convert_document.delay(
        input_filename=unique_filename,
        conversion_type=conversion_type.value,
        original_filename=file.filename,
    )

    return ConversionResponse(
        task_id=result.id,
        status="PENDING",
        filename=file.filename,
        conversion_type=conversion_type,
    )


@app.get("/convert/status/{task_id}", response_model=ConversionStatusResponse)
async def get_conversion_status(task_id: str):
    """Get the status of a conversion task.

    Returns progress, status, and download URL when complete.
    """
    result = AsyncResult(task_id, app=celery_app)

    response = ConversionStatusResponse(
        task_id=task_id,
        status=result.status,
    )

    if result.ready():
        if result.successful():
            task_result = result.result
            response.result = task_result
            if task_result.get("success"):
                response.download_url = f"/convert/download/{task_id}"
            else:
                response.error = task_result.get("error", "Unknown error")
        else:
            response.error = str(result.result)
    elif result.status == "PROCESSING":
        meta = result.info
        if meta and isinstance(meta, dict):
            response.progress = meta.get("progress")

    return response


@app.get("/convert/download/{task_id}")
async def download_converted_file(task_id: str):
    """Download a converted file.

    The task must be completed successfully before downloading.
    """
    result = AsyncResult(task_id, app=celery_app)

    if not result.ready():
        raise HTTPException(status_code=400, detail="Conversion not yet complete")

    if not result.successful():
        raise HTTPException(status_code=400, detail="Conversion failed")

    task_result = result.result
    if not task_result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=task_result.get("error", "Conversion failed"),
        )

    output_path = Path(task_result.get("output_path", ""))
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Converted file not found")

    return FileResponse(
        path=output_path,
        filename=task_result.get("converted_filename"),
        media_type="application/octet-stream",
    )


@app.post("/convert/sync")
async def convert_sync(
    file: UploadFile = File(..., description="File to convert"),
    conversion_type: ConversionType = Form(..., description="Type of conversion"),
    engine: str = Form(
        default="auto",
        description="PDF to Word engine: 'auto', 'marker' (professional), 'pdf2docx', or 'doctr'"
    ),
):
    """Convert a file synchronously (without Celery/Redis).

    Use this endpoint for testing or when Redis is not available.
    For production, use /convert/upload with background processing.

    For PDF to Word conversions, you can select the conversion engine:
    - auto: Automatically select based on PDF type (default)
    - marker: Use marker-pdf for professional-grade conversion (recommended)
    - pdf2docx: Use pdf2docx library
    - doctr: Use doctr OCR (for scanned documents)
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # Validate engine parameter
    valid_engines = ["auto", "marker", "pdf2docx", "doctr"]
    if engine not in valid_engines:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid engine '{engine}'. Must be one of: {valid_engines}"
        )

    # Generate unique filename
    file_ext = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    upload_path = UPLOAD_DIR / unique_filename

    # Save uploaded file
    try:
        async with aiofiles.open(upload_path, "wb") as f:
            content = await file.read()
            await f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}") from e

    # Perform conversion synchronously
    try:
        output_path = convert_file(upload_path, conversion_type, engine=engine)

        # Clean up input file
        if upload_path.exists():
            upload_path.unlink()

        return FileResponse(
            path=output_path,
            filename=output_path.name,
            media_type="application/octet-stream",
        )
    except ConversionError as e:
        # Clean up input file on error
        if upload_path.exists():
            upload_path.unlink()
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        if upload_path.exists():
            upload_path.unlink()
        raise HTTPException(status_code=500, detail=f"Conversion failed: {e}") from e


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=True,
    )
