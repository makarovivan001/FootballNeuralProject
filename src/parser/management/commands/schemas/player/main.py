from decimal import Decimal

from pydantic import BaseModel, model_validator, field_validator, Field


class ParserPlayerCreateDTO(BaseModel):
    identifier: int = Field(alias="id")
    club_id: int | None = None
    statistic_id: int | None = None
    photo_url: str
    surname: str = ''
    name: str
    number: int | None
    height: int | None
    age: int | None
    country: str = Field(alias='cname')
    role_ids: list[int] = []
    position_id: int | None
    preferred_foot: str | None = None

    @model_validator(mode="before")
    @classmethod
    def validate_identifier(cls, values: dict) -> dict:
        club_logo_url = "https://images.fotmob.com/image_resources/playerimages/{player_id}.png"

        values["photo_url"] = club_logo_url.format(player_id=values["id"])

        fullname = values['name'].split()
        if len(fullname) == 2:
            values['surname'] = fullname[1]
            values['name'] = fullname[0]

        height = None
        age = None
        cname = ''
        preferred_foot = None
        number = None
        for player_info in values["playerInformation"]:
            if player_info['title'] == 'Age':
                age = player_info["value"]["numberValue"]
            elif player_info['title'] == 'Height':
                height = player_info["value"]["numberValue"]
            elif player_info['title'] == 'Preferred foot':
                preferred_foot = player_info["value"]["key"]
            elif player_info['title'] == 'Country' or player_info['title'] == 'Country/Region':
                cname = player_info["value"]["fallback"]
            elif player_info['title'] == 'Shirt':
                number = player_info["value"]["fallback"]

        values.update({
            "age": age,
            "height": height,
            "preferred_foot": preferred_foot,
            "cname": cname,
            "number": number,
        })
        return values


class ParserPlayerUpdateDTO(ParserPlayerCreateDTO):
    id: int | None = None


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