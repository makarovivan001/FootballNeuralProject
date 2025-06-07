from pydantic import BaseModel, model_validator, field_validator, Field


class ParserClubCreateDTO(BaseModel):
    identifier: int = Field(alias="id")
    name: str
    photo_url: str
    stadium_name: str
    stadium_count_of_sits: int
    city_name: str = Field(alias="country")
    placement: dict = {}

    @model_validator(mode="before")
    @classmethod
    def validate_identifier(cls, values: dict) -> dict:
        club_logo_url = "https://images.fotmob.com/image_resources/logo/teamlogo/{club_id}.png"
        values["details"]["photo_url"] = club_logo_url.format(club_id=values["details"]["id"])
        try:
            values["details"]["stadium_name"] = values['overview']['venue']['widget']['name']
            values["details"]["stadium_count_of_sits"] = values['overview']['venue']['statPairs'][1][1]
        except:
            values["details"]["stadium_name"] = ""
            values["details"]["stadium_count_of_sits"] = 0


        return values["details"]

class ParserClubUpdateDTO(ParserClubCreateDTO):
    id: int


class ParserClubIdRetrieveDTO(BaseModel):
    id: int
    identifier: int

    class Config:
        from_attributes = True