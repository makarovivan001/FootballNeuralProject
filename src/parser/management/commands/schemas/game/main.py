from datetime import datetime, timezone

from pydantic import BaseModel, model_validator


class ParserGameCreateDTO(BaseModel):
    identifier: int
    game_date: datetime
    is_finished: bool
    home_club_id: int
    away_club_id: int
    home_score: int = 0
    away_score: int = 0
    home_club_placement: list = []
    away_club_placement: list = []

    home_players: list[int] = []
    away_players: list[int] = []

    season_id: int
    tour: int = 0
    # Лучшего игрока получаем позже

    @model_validator(mode="before")
    @classmethod
    def data_validator(cls, values: dict) -> dict:
        game_date = datetime.strptime(values['general']['matchTimeUTCDate'], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)

        try:
            try:
                score = values['header']['status']['scoreStr']
            except KeyError:
                score = '0 - 0'

            scores = list(map(int, score.split(' - ') if score else [0, 0]))

            values.update({
                "identifier": values['general']['matchId'],
                "is_finished": values['general']['finished'],
                "game_date": game_date,
                "home_score": scores[0],
                "away_score": scores[1],
            })
        except Exception as e:
            print(e)

        return values


class ParserGameUpdateDTO(ParserGameCreateDTO):
    id: int | None = None


class ParserGameShortRetrieveDTO(BaseModel):
    id: int
    identifier: int
    is_finished: bool
    home_club_id: int
    away_club_id: int

    class Config:
        from_attributes = True