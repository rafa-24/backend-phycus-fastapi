from datetime import UTC, datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class SiigoDetail(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    store_id: int = Field(foreign_key="stores.id", index=True)

    user_api: Optional[str] = Field(default=None)
    access_key: Optional[str] = Field(default=None)

    access_token: Optional[str] = Field(default=None) # llave de acceso generada por siigo
    expiration_time: Optional[float] = Field(default=None) # tiempo de expiracion del token
    token_type: Optional[str] = Field(default=None)
    status_connection: Optional[bool] = Field(default=None)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))