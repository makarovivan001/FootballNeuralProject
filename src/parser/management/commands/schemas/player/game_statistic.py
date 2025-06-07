from decimal import Decimal

from pydantic import BaseModel


class ParserPlayerGameStatisticCreateDTO(BaseModel):
    game_id: int
    player_id: int
    rating_title: Decimal = Decimal(0)
    minutes_played: int = 0
    goals: int = 0
    assists: int = 0
    total_shots: int = 0
    accurate_passes: str = ''
    chances_created: int = 0
    touches: int = 0
    touches_opp_box: int = 0
    passes_into_final_third: int = 0
    accurate_crosses: str = ''
    long_balls_accurate: str = ''
    corners: int = 0
    dispossessed: int = 0
    tackles_succeeded: str = ''
    clearances: int = 0
    headed_clearance: int = 0
    interceptions: int = 0
    defensive_actions: int = 0
    recoveries: int = 0
    dribbled_past: int = 0
    duel_won: int = 0
    duel_lost: int = 0
    ground_duels_won: str = ''
    aerials_won: str = ''
    was_fouled: int = 0
    fouls: int = 0
    saves: int = 0
    goals_conceded: int = 0
    keeper_diving_save: int = 0
    saves_inside_box: int = 0
    keeper_sweeper: int = 0
    punches: int = 0
    player_throws: int = 0
    keeper_high_claim: int = 0


class ParserPlayerGameStatisticUpdateDTO(ParserPlayerGameStatisticCreateDTO):
    id: int