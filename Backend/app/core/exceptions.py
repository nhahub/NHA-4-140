from fastapi import HTTPException


class NotFoundException(HTTPException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=404, detail=detail)


class UnauthorizedException(HTTPException):
    def __init__(self, detail: str = "Not authenticated"):
        super().__init__(status_code=401, detail=detail)


class ForbiddenException(HTTPException):
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(status_code=403, detail=detail)


class ConflictException(HTTPException):
    def __init__(self, detail: str = "Conflict"):
        super().__init__(status_code=409, detail=detail)


class FileTooLargeException(HTTPException):
    def __init__(self, detail: str = "File too large"):
        super().__init__(status_code=413, detail=detail)


class UnsupportedMediaTypeException(HTTPException):
    def __init__(self, detail: str = "Unsupported file type"):
        super().__init__(status_code=415, detail=detail)


class StorageUploadException(HTTPException):
    def __init__(self, detail: str = "File upload failed"):
        super().__init__(status_code=500, detail=detail)
