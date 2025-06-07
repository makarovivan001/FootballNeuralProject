from decimal import Decimal

from pydantic import BaseModel


class ParserPlayerStatisticCreateDTO(BaseModel):
    all_goals: int = 0
    all_ShotsOnTarget: int = 0
    all_yellow_cards: int = 0
    all_red_cards: int = 0
    all_assists: int = 0
    all_chances_created: int = 0
    all_dribbles_succeeded: int = 0
    all_dispossessed: int = 0

    started: int = 0
    matches_uppercase: int = 0
    minutes_played: int = 0
    rating: Decimal = Decimal(0)
    goals: Decimal = Decimal(0)
    shots: Decimal = Decimal(0)
    ShotsOnTarget: Decimal = Decimal(0)
    assists: Decimal = Decimal(0)
    successful_passes: Decimal = Decimal(0)
    successful_passes_accuracy: Decimal = Decimal(0)
    long_balls_accurate: Decimal = Decimal(0)
    long_ball_succeeeded_accuracy: Decimal = Decimal(0)
    chances_created: Decimal = Decimal(0)
    dribbles_succeeded: Decimal = Decimal(0)
    won_contest_subtitle: Decimal = Decimal(0)
    touches: Decimal = Decimal(0)
    touches_opp_box: Decimal = Decimal(0)
    dispossessed: Decimal = Decimal(0)
    fouls_won: Decimal = Decimal(0)
    tackles_succeeded: Decimal = Decimal(0)
    tackles_succeeded_percent: Decimal = Decimal(0)
    duel_won: Decimal = Decimal(0)
    duel_won_percent: Decimal = Decimal(0)
    aerials_won: Decimal = Decimal(0)
    aerials_won_percent: Decimal = Decimal(0)
    interceptions: Decimal = Decimal(0)
    shot_blocked: Decimal = Decimal(0)
    fouls: Decimal = Decimal(0)
    recoveries: Decimal = Decimal(0)
    poss_won_att_3rd_team_title: Decimal = Decimal(0)
    dribbled_past: Decimal = Decimal(0)
    yellow_cards: Decimal = Decimal(0)
    red_cards: Decimal = Decimal(0)
    crosses_succeeeded: Decimal = Decimal(0)
    crosses_succeeeded_accuracy: Decimal = Decimal(0)

    saves: Decimal = Decimal(0)
    save_percentage: Decimal = Decimal(0)
    goals_conceded: Decimal = Decimal(0)
    clean_sheet_team_title: Decimal = Decimal(0)
    penalties_faced: Decimal = Decimal(0)
    penalty_goals_conceded: Decimal = Decimal(0)
    penalty_saves: Decimal = Decimal(0)
    error_led_to_goal: Decimal = Decimal(0)
    keeper_sweeper: Decimal = Decimal(0)
    keeper_high_claim: Decimal = Decimal(0)


class ParserPlayerStatisticUpdateDTO(ParserPlayerStatisticCreateDTO):
    id: int