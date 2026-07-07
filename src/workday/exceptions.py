"""Workday client exception types."""

class WorkdayAPIError(Exception):
    """Raised for Workday transport errors or non-success responses."""
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
