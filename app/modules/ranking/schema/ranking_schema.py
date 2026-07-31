from sqlmodel import SQLModel


class RankingCreate(SQLModel):
    product_id: int


class RankingResponse(SQLModel):
    id: int
    product_id: int
    score: int
    reason: str
    image_url: str