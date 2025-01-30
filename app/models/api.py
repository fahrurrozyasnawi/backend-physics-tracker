from pydantic import BaseModel, Field
from typing import Optional, Any


class CustomResponse(BaseModel):
    success: bool
    message: Optional[str] = Field(None)
    data: Optional[Any] = None
