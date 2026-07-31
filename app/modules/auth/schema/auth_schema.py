from sqlmodel import SQLModel


class LoginRequest(SQLModel):
    email: str
    password: str


class AuthResponse(SQLModel):
    access_token: str
    user_id: int
    role_id: int
    role_name: str | None = None
    store_id: int | None = None
    collaborator_role: str | None = None
    is_store_owner: bool = False


class PasswordRecoveryRequest(SQLModel):
    email: str


class PasswordRecoveryResponse(SQLModel):
    email: str


class ChangePasswordRequest(SQLModel):
    email: str
    code: int
    password: str


class ChangePasswordResponse(SQLModel):
    email: str
