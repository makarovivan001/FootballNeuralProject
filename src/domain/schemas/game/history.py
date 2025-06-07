from pydantic import BaseModel

from domain.schemas.player.main import PlayerShortRetrieveDTO


class HistoryActionRetrieveDTO(BaseModel):
    name: str

    class Config:
        from_attributes = True


class HistoryRetrieveDTO(BaseModel):
    player: PlayerShortRetrieveDTO | None
    minutes: int
    is_home: bool
    action: HistoryActionRetrieveDTO
    overload_minutes: int | None
    swap: list | None

    class Config:
        from_attributes = True