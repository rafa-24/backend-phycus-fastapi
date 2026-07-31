from sqlmodel import Field, SQLModel


class Ranking(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    product_id: int
    score: int
    reason: str
    image_url: str