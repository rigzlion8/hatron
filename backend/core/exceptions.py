"""Custom exception hierarchy for the ERP system."""

from typing import Any


class ERPException(Exception):
    """Base exception for all ERP errors."""

    def __init__(self, message: str, code: str = "ERP_ERROR", status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(ERPException):
    """Resource not found."""

    def __init__(self, resource: str = "Resource", resource_id: Any = None):
        detail = f"{resource} not found"
        if resource_id:
            detail = f"{resource} with id '{resource_id}' not found"
        super().__init__(message=detail, code="NOT_FOUND", status_code=404)


class AlreadyExistsError(ERPException):
    """Resource already exists (duplicate)."""

    def __init__(self, resource: str = "Resource", field: str = ""):
        detail = f"{resource} already exists"
        if field:
            detail = f"{resource} with this {field} already exists"
        super().__init__(message=detail, code="ALREADY_EXISTS", status_code=409)


class ValidationError(ERPException):
    """Business logic validation error."""

    def __init__(self, message: str = "Validation failed"):
        super().__init__(message=message, code="VALIDATION_ERROR", status_code=422)


class AuthenticationError(ERPException):
    """Authentication failure."""

    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(message=message, code="AUTHENTICATION_ERROR", status_code=401)


class PermissionDeniedError(ERPException):
    """Insufficient permissions."""

    def __init__(self, message: str = "Permission denied"):
        super().__init__(message=message, code="PERMISSION_DENIED", status_code=403)


class TenantError(ERPException):
    """Tenant-related error."""

    def __init__(self, message: str = "Tenant error"):
        super().__init__(message=message, code="TENANT_ERROR", status_code=400)
