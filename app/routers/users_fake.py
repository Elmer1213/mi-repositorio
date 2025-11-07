from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/users", tags=["users (fake)"])

class FakeUser(BaseModel):
    id: int | None = None
    name: str
    email: str

fake_users = []
next_id = 1

@router.get("/")
def get_users():
    return fake_users

@router.post("/")
def add_user(user: FakeUser):
    global next_id
    user.id = next_id
    next_id += 1
    fake_users.append(user)
    return {"message": "Usuario agregado correctamente", "user": user}
