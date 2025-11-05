from pydantic import BaseModel


#definir y validar
class UserBase(BaseModel):
    name: str
    email: str

class UserCreate(UserBase):
    pass

class UserResponse(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True