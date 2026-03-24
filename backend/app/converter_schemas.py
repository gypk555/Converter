"""Pydantic schemas for document conversion API."""

from enum import Enum

from pydantic import BaseModel, Field


class ConversionType(str, Enum):
    """Supported conversion types."""

    PDF_TO_WORD = "pdf_to_word"
    WORD_TO_PDF = "word_to_pdf"
    WORD_TO_EXCEL = "word_to_excel"
    EXCEL_TO_WORD = "excel_to_word"


class ConversionRequest(BaseModel):
    """Request schema for file conversion."""

    conversion_type: ConversionType = Field(
        ...,
        description="Type of conversion to perform",
    )


class ConversionResponse(BaseModel):
    """Response schema after file upload for conversion."""

    task_id: str = Field(..., description="Celery task ID for tracking progress")
    status: str = Field(..., description="Initial task status")
    filename: str = Field(..., description="Original filename")
    conversion_type: ConversionType = Field(..., description="Requested conversion type")


class ConversionStatusResponse(BaseModel):
    """Response schema for conversion status check."""

    task_id: str = Field(..., description="Celery task ID")
    status: str = Field(
        ..., description="Current task status (PENDING, PROCESSING, SUCCESS, FAILURE)"
    )
    progress: float | None = Field(None, description="Progress percentage (0-100)")
    result: dict | None = Field(None, description="Conversion result if completed")
    error: str | None = Field(None, description="Error message if failed")
    download_url: str | None = Field(None, description="URL to download converted file")


class ConversionResultResponse(BaseModel):
    """Response schema for completed conversion."""

    success: bool = Field(..., description="Whether conversion was successful")
    original_filename: str = Field(..., description="Original uploaded filename")
    converted_filename: str = Field(..., description="Name of converted file")
    conversion_type: ConversionType = Field(..., description="Type of conversion performed")
    file_size: int = Field(..., description="Size of converted file in bytes")
    download_url: str = Field(..., description="URL to download the converted file")


class SupportedFormatsResponse(BaseModel):
    """Response schema for supported conversion formats."""

    conversions: list[dict] = Field(..., description="List of supported conversions")
