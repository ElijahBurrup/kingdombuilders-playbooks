from pydantic import BaseModel, EmailStr


class SubscribeRequest(BaseModel):
    email: EmailStr
    source: str = "salmon-journey-ch1"


class SubscribeResponse(BaseModel):
    message: str
