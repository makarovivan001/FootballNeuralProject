from decimal import Decimal

from pydantic import BaseModel


class StatisticRetrieveDTO(BaseModel):
    xg: Decimal
    goal_attempts: int
    shots: int
    saves: int
    corners: int
    fouls: int
    passes: int
    tackles: int
    yellow_cards: int
    red_cards: int
    shots_on_target: int
    shots_off_target: int
    blocked_shots: int
    shots_inside_box: int
    shots_outside_box: int
    big_chances_missed: int
    offsides: int
    possession: Decimal
    big_chances: int

    class Config:
        from_attributes = True

class ClubsStatisticRetrieveDTO(BaseModel):
    home_club_statistic: StatisticRetrieveDTO
    away_club_statistic: StatisticRetrieveDTO