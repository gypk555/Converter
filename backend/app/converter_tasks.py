"""Celery tasks for document conversion."""

import os

from celery.utils.log import get_task_logger

from app.celery_app import celery_app
from app.converter_schemas import ConversionType
from app.converter_service import (
    OUTPUT_DIR,
    UPLOAD_DIR,
    ConversionError,
    cleanup_file,
    convert_file,
)

logger = get_task_logger(__name__)


@celery_app.task(
    bind=True,
    name="app.converter_tasks.convert_document",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    max_retries=2,
)
def convert_document(
    self,
    input_filename: str,
    conversion_type: str,
    original_filename: str,
) -> dict:
    """Convert a document in the background.

    Args:
        input_filename: Name of the uploaded file in UPLOAD_DIR.
        conversion_type: Type of conversion (from ConversionType enum).
        original_filename: Original name of the uploaded file.

    Returns:
        dict: Conversion result with status and file info.
    """
    task_id = self.request.id
    logger.info(f"Starting conversion task {task_id}: {original_filename} -> {conversion_type}")

    input_path = UPLOAD_DIR / input_filename

    try:
        # Update state to processing
        self.update_state(
            state="PROCESSING",
            meta={
                "progress": 10,
                "status": "Starting conversion",
                "original_filename": original_filename,
            },
        )

        # Validate input file exists
        if not input_path.exists():
            raise ConversionError(f"Input file not found: {input_filename}")

        # Update progress
        self.update_state(
            state="PROCESSING",
            meta={
                "progress": 30,
                "status": "Converting document",
                "original_filename": original_filename,
            },
        )

        # Perform conversion
        conv_type = ConversionType(conversion_type)
        output_path = convert_file(input_path, conv_type)

        # Update progress
        self.update_state(
            state="PROCESSING",
            meta={
                "progress": 90,
                "status": "Finalizing",
                "original_filename": original_filename,
            },
        )

        # Get file info
        file_size = output_path.stat().st_size
        converted_filename = output_path.name

        logger.info(f"Conversion complete: {converted_filename} ({file_size} bytes)")

        # Cleanup input file
        cleanup_file(input_path)

        return {
            "status": "completed",
            "task_id": task_id,
            "success": True,
            "original_filename": original_filename,
            "converted_filename": converted_filename,
            "conversion_type": conversion_type,
            "file_size": file_size,
            "output_path": str(output_path),
        }

    except ConversionError as e:
        logger.error(f"Conversion error in task {task_id}: {e}")
        cleanup_file(input_path)
        return {
            "status": "failed",
            "task_id": task_id,
            "success": False,
            "error": str(e),
            "original_filename": original_filename,
            "conversion_type": conversion_type,
        }
    except Exception as e:
        logger.exception(f"Unexpected error in task {task_id}: {e}")
        cleanup_file(input_path)
        raise  # Let Celery handle retry


@celery_app.task(
    bind=True,
    name="app.converter_tasks.cleanup_old_files",
)
def cleanup_old_files(self, max_age_hours: int = 24) -> dict:
    """Cleanup old temporary files.

    Args:
        max_age_hours: Remove files older than this many hours.

    Returns:
        dict: Cleanup statistics.
    """
    import time

    task_id = self.request.id
    logger.info(f"Starting cleanup task {task_id}")

    max_age_seconds = max_age_hours * 3600
    current_time = time.time()
    removed_count = 0
    removed_size = 0

    for directory in [UPLOAD_DIR, OUTPUT_DIR]:
        if not directory.exists():
            continue

        for filepath in directory.iterdir():
            if filepath.is_file():
                file_age = current_time - filepath.stat().st_mtime
                if file_age > max_age_seconds:
                    try:
                        file_size = filepath.stat().st_size
                        os.remove(filepath)
                        removed_count += 1
                        removed_size += file_size
                        logger.debug(f"Removed old file: {filepath}")
                    except OSError as e:
                        logger.warning(f"Failed to remove {filepath}: {e}")

    logger.info(f"Cleanup complete: removed {removed_count} files ({removed_size} bytes)")

    return {
        "status": "completed",
        "task_id": task_id,
        "removed_count": removed_count,
        "removed_size_bytes": removed_size,
    }
