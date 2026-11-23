from typing import Optional
from pydantic import BaseModel


class UserRegister(BaseModel):
    business_name: str
    email: str
    password: str
    whatsapp: str = ""
    plan_type: str = "free"


class UserLogin(BaseModel):
    email: str
    password: str


class ProductCreate(BaseModel):
    name: str
    price: float
    currency: str = "Bs"
    image_data: Optional[str] = None

class UserAdminUpdate(BaseModel):
    business_name: str
    email: str
    whatsapp: str = ""
    plan_type: str = "free"
    flyers_generated: int = 0