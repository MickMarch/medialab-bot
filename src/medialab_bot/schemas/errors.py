from pydantic import BaseModel


class ErrorResponse(BaseModel):
    status: str
    code: str
    detail: str
