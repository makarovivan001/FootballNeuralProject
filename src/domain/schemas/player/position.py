from pydantic import BaseModel


class PlayerPositionRetrieveDTO(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True