from decimal import Decimal

from pydantic import BaseModel


class StatisticRetrieveDTO(BaseModel):
    big_chance: int
    big_chance_missed_title: int
    fouls: int
    corners: int
    total_shots: int
    shots_on_target: int
    shots_off_target: int
    blocked_shots: int
    shots_woodwork: int
    shots_inside_box: int
    shots_outside_box: int
    passes: int
    accurate_passes: int
    accurate_passes_persent: int
    own_half_passes: int
    opposition_half_passes: int
    long_balls_accurate: int
    long_balls_accurate_persent: int
    accurate_crosses: int
    accurate_crosses_persent: int
    player_throws: int
    touches_opp_box: int | None
    offsides: int
    tackles_succeeded: int
    tackles_succeeded_persent: int
    interceptions: int
    shot_blocks: int
    clearances: int
    keeper_saves: int
    duel_won: int
    ground_duels_won: int
    ground_duels_won_persent: int
    aerials_won: int
    aerials_won_persent: int
    dribbles_succeeded: int
    dribbles_succeeded_persent: int
    yellow_cards: int
    red_cards: int

    class Config:
        from_attributes = True

class ClubsStatisticRetrieveDTO(BaseModel):
    home_club_statistic: StatisticRetrieveDTO | None
    away_club_statistic: StatisticRetrieveDTO | None