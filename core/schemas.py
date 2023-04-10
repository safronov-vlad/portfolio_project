from pydantic import BaseModel
from typing import Optional


class ResponseSchema(BaseModel):
    data: Optional[dict]
    response_message: Optional[str]


class AuthorizationSchema(BaseModel):
    username: str
    password: str
