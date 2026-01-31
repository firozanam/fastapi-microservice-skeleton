"""
Common schemas for standard API responses.
"""
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class PaginationMeta(BaseModel):
    """Pagination metadata."""

    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    total_items: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_previous: bool = Field(..., description="Whether there is a previous page")


class SuccessResponse(BaseModel, Generic[DataT]):
    """Standard success response schema."""

    success: bool = Field(default=True, description="Request success status")
    message: str = Field(..., description="Response message")
    data: Optional[DataT] = Field(None, description="Response data")


class PaginatedResponse(BaseModel, Generic[DataT]):
    """Paginated response schema."""

    success: bool = Field(default=True, description="Request success status")
    message: str = Field(..., description="Response message")
    data: List[DataT] = Field(..., description="List of items")
    pagination: PaginationMeta = Field(..., description="Pagination metadata")


class ErrorDetail(BaseModel):
    """Error detail schema."""

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    success: bool = Field(default=False, description="Request success status")
    error: ErrorDetail = Field(..., description="Error details")


class ValidationErrorDetail(BaseModel):
    """Validation error detail schema."""

    code: str = Field(default="validation_error", description="Error code")
    message: str = Field(default="Validation failed", description="Error message")
    errors: List["FieldError"] = Field(..., description="List of field errors")


class ValidationErrorResponse(BaseModel):
    """Validation error response schema."""

    success: bool = Field(default=False, description="Request success status")
    error: ValidationErrorDetail = Field(..., description="Validation error details")


class FieldError(BaseModel):
    """Field error schema."""

    field: str = Field(..., description="Field name")
    message: str = Field(..., description="Error message")
    type: str = Field(..., description="Error type")


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    environment: str = Field(..., description="Environment name")
    checks: dict = Field(..., description="Health check results")


class MessageResponse(BaseModel):
    """Simple message response schema."""

    success: bool = Field(default=True, description="Request success status")
    message: str = Field(..., description="Response message")
