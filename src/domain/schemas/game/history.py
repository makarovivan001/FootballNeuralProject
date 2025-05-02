from pydantic import BaseModel

from domain.enums.game_history_action import GameHistoryAction
from domain.schemas.player.main import PlayerShortRetrieveDTO


class HistoryRetrieveDTO(BaseModel):
    player: PlayerShortRetrieveDTO
    action: GameHistoryAction
    minutes: int

    class Config:
        from_attributes = True