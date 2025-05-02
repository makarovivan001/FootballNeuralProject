from pydantic import BaseModel


class PlayerShortStatisticRetrieveDTO(BaseModel):
    # minutes_played: int
    goals: int
    assists: int
    yellow_cards: int
    red_cards: int
