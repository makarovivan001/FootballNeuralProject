from pydantic import BaseModel


class HistoryCreateDTO(BaseModel):
    game_id: int
    player_id: int | None
    is_home: bool
    action_id: int
    minutes: int
    overload_minutes: int | None
    swap: list | None


class HistoryUpdateDTO(HistoryCreateDTO):
    id: int