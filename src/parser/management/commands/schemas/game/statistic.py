from pydantic import BaseModel, Field


class ParserGameStatisticCreateDTO(BaseModel):
    club_id: int
    game_id: int
    big_chance: int | None = None
    big_chance_missed_title: int | None = None
    fouls: int | None = None
    corners: int | None = None
    total_shots: int | None = None
    shots_on_target: int | None = Field(alias='ShotsOnTarget', default=None)
    shots_off_target: int | None = Field(alias='ShotsOffTarget', default=None)
    blocked_shots: int | None = None
    shots_woodwork: int | None = None
    shots_inside_box: int | None = None
    shots_outside_box: int | None = None
    passes: int | None = None
    accurate_passes: int | None = None
    accurate_passes_persent: int | None = None
    own_half_passes: int | None = None
    opposition_half_passes: int | None = None
    long_balls_accurate: int | None = None
    long_balls_accurate_persent: int | None = None
    accurate_crosses: int | None = None
    accurate_crosses_persent: int | None = None
    player_throws: int | None = None
    touches_opp_box: int | None = None
    offsides: int | None = Field(alias='Offsides', default=None)
    tackles_succeeded: int | None = None
    tackles_succeeded_persent: int | None = None
    interceptions: int | None = None
    shot_blocks: int | None = None
    clearances: int | None = None
    keeper_saves: int | None = None
    duel_won: int | None = None
    ground_duels_won: int | None = None
    ground_duels_won_persent: int | None = None
    aerials_won: int | None = None
    aerials_won_persent: int | None = None
    dribbles_succeeded: int | None = None
    dribbles_succeeded_persent: int | None = None
    yellow_cards: int | None = None
    red_cards: int | None = None


class ParserGameStatisticUpdateDTO(ParserGameStatisticCreateDTO):
    id: int

