from datetime import datetime

from pydantic import BaseModel

from domain.schemas.club.main import ClubShortRetrieveDTO
from domain.schemas.player.main import PlayerBestRetrieveDTO


class GameShortRetrieveDTO(BaseModel):
    id: int
    game_date: datetime
    is_finished: bool
    home_club: ClubShortRetrieveDTO
    away_club: ClubShortRetrieveDTO
    home_score: int
    away_score: int


    class Config:
        from_attributes = True


class GameRetrieveDTO(GameShortRetrieveDTO):
    best_player: PlayerBestRetrieveDTO | None
    home_club_placement: list
    away_club_placement: list
    home_players: list
    away_players: list


