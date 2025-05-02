from decimal import Decimal

from pydantic import BaseModel, model_validator, field_validator, Field


class ParserPlayerCreateDTO(BaseModel):
    identifier: int = Field(alias="id")
    club_id: int | None = None
    photo_url: str
    surname: str = ''
    name: str
    height: int | None
    age: int | None
    country: str = Field(alias='cname')
    position_id: int | None = None

    @model_validator(mode="before")
    @classmethod
    def validate_identifier(cls, values: dict) -> dict:
        club_logo_url = "https://images.fotmob.com/image_resources/playerimages/{player_id}.png"

        values["photo_url"] = club_logo_url.format(player_id=values["id"])

        fullname = values['name'].split()
        if len(fullname) == 2:
            values['surname'] = fullname[1]
            values['name'] = fullname[0]

        return values


class ParserPlayerIdentifierRetrieveDTO(BaseModel):
    id: int
    identifier: int
    statistic_id: int | None

    class Config:
        from_attributes = True


class PlayerPositionIdRetrieveDTO(BaseModel):
    id: int

    class Config:
        from_attributes = True


class ParserStatisticIdDTO(BaseModel):
    id: int

    class Config:
        from_attributes = True


class ParserPlayerStatisticCreateDTO(BaseModel):
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