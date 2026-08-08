from pydantic import BaseModel
from typing import List, Optional

# Modelo para cada objeto dentro de la lista 'errors'
class SiigoErrorItem(BaseModel):
    code: str
    message: str
    params: List[str] = []
    detail: Optional[str] = None

# Modelo principal para la respuesta de error de Siigo
class SiigoErrorResponse(BaseModel):
    status: int
    errors: List[SiigoErrorItem]

# Modelo para la respuesta exitosa
class SiigoTokenSuccess(BaseModel):
    access_token: str
    expires_in: int
    token_type: str = "Bearer"
    scope: Optional[str] = None