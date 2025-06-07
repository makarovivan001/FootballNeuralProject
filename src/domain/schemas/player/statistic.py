from decimal import Decimal

from pydantic import BaseModel

from domain.schemas.player.position import PlayerPositionRetrieveDTO


class PlayerShortStatisticRetrieveDTO(BaseModel):
    minutes_played: int
    all_goals: int
    all_yellow_cards: int
    all_red_cards: int
    all_assists: int
    rating: Decimal = Decimal(0.00)


    class Config:
        from_attributes = True

class PlayerStatisticRetrieveDTO(PlayerShortStatisticRetrieveDTO):
    player_id: int | None = None
    started: int
    matches_uppercase: int
    goals: Decimal = Decimal(0.00)
    shots: Decimal = Decimal(0.00)
    ShotsOnTarget: Decimal = Decimal(0.00)
    assists: Decimal = Decimal(0.00)
    successful_passes: Decimal = Decimal(0.00)
    successful_passes_accuracy: Decimal = Decimal(0.00)
    long_balls_accurate: Decimal = Decimal(0.00)
    long_ball_succeeeded_accuracy: Decimal = Decimal(0.00)
    chances_created: Decimal = Decimal(0.00)
    dribbles_succeeded: Decimal = Decimal(0.00)
    won_contest_subtitle: Decimal = Decimal(0.00)
    touches: Decimal = Decimal(0.00)
    touches_opp_box: Decimal = Decimal(0.00)
    dispossessed: Decimal = Decimal(0.00)
    fouls_won: Decimal = Decimal(0.00)
    tackles_succeeded: Decimal = Decimal(0.00)
    tackles_succeeded_percent: Decimal = Decimal(0.00)
    duel_won: Decimal = Decimal(0.00)
    duel_won_percent: Decimal = Decimal(0.00)
    aerials_won: Decimal = Decimal(0.00)
    aerials_won_percent: Decimal = Decimal(0.00)
    interceptions: Decimal = Decimal(0.00)
    shot_blocked: Decimal = Decimal(0.00)
    fouls: Decimal = Decimal(0.00)
    recoveries: Decimal = Decimal(0.00)
    poss_won_att_3rd_team_title: Decimal = Decimal(0.00)
    dribbled_past: Decimal = Decimal(0.00)
    yellow_cards: Decimal = Decimal(0.00)
    red_cards: Decimal = Decimal(0.00)
    crosses_succeeeded: Decimal = Decimal(0.00)
    crosses_succeeeded_accuracy: Decimal = Decimal(0.00)
    all_ShotsOnTarget: int
    all_chances_created: int
    all_dribbles_succeeded: int
    all_dispossessed: int
    saves: Decimal = Decimal(0.00)
    save_percentage: Decimal = Decimal(0.00)
    goals_conceded: Decimal = Decimal(0.00)
    clean_sheet_team_title: Decimal = Decimal(0.00)
    penalties_faced: Decimal = Decimal(0.00)
    penalty_goals_conceded: Decimal = Decimal(0.00)
    penalty_saves: Decimal = Decimal(0.00)
    error_led_to_goal: Decimal = Decimal(0.00)
    keeper_sweeper: Decimal = Decimal(0.00)
    keeper_high_claim: Decimal = Decimal(0.00)
