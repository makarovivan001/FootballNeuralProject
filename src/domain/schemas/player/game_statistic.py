from decimal import Decimal

from pydantic import BaseModel

from domain.schemas.player.main import PlayerShortRetrieveDTO


class PlayerGameStatisticShortRetrieveDTO(BaseModel):
    game_id: int | None = None
    rating_title: Decimal = Decimal(0.00)
    minutes_played: int = 0
    goals: int = 0
    assists: int = 0
    chances_created: int = 0
    duel_won: int = 0
    duel_lost: int = 0
    was_fouled: int = 0
    fouls: int = 0


    class Config:
        from_attributes = True

class PlayerGameStatisticRetrieveDTO(PlayerGameStatisticShortRetrieveDTO):
    player: PlayerShortRetrieveDTO
    total_shots: int
    accurate_passes: str
    touches: int
    touches_opp_box: int
    passes_into_final_third: int
    accurate_crosses: str
    long_balls_accurate: str
    corners: int
    dispossessed: int
    tackles_succeeded: str
    clearances: int
    headed_clearance: int
    interceptions: int
    defensive_actions: int
    recoveries: int
    dribbled_past: int
    ground_duels_won: str
    aerials_won: str
