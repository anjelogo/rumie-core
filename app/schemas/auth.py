from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.user import Gender, Role, User


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    role: Role
    age: int = Field(ge=18)
    gender: Gender
    phone: str | None = None
    capacity: int = Field(default=1, ge=1)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class RefreshIn(BaseModel):
    refresh: str


class TokensOut(BaseModel):
    access: str
    refresh: str


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    phone: str | None
    role: Role
    age: int
    gender: Gender
    profile_photo_url: str | None

    @classmethod
    def from_doc(cls, u: User) -> "UserOut":
        return cls(
            id=u.id,
            email=u.email,
            phone=u.phone,
            role=u.role,
            age=u.age,
            gender=u.gender,
            profile_photo_url=u.profile_photo_url,
        )


class RegisterOut(BaseModel):
    user: UserOut
    tokens: TokensOut
