from pydantic import BaseModel, EmailStr


class SubscribeRequest(BaseModel):
    email: EmailStr
    source: str = "catalog"


class SubscribeResponse(BaseModel):
    message: str
