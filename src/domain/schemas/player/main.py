from django.db.models.fields.files import ImageFieldFile
from pydantic import BaseModel, field_validator

from domain.schemas.club.main import ClubShortRetrieveDTO
from domain.schemas.player.statistic import PlayerShortStatisticRetrieveDTO


class PlayerShortRetrieveDTO(BaseModel):
    id: int
    photo: str
    surname: str
    name: str

    class Config:
        from_attributes = True

    @field_validator('photo', mode="before")
    @staticmethod
    def image_validator(image: ImageFieldFile | None) -> str:
        if image:
            return image.url
        return ""

class PlayerBestRetrieveDTO(PlayerShortRetrieveDTO):
    club: ClubShortRetrieveDTO


class PlayerStatsRetrieveDTO(BaseModel):
    id: int
    surname: str
    name: str
    club: ClubShortRetrieveDTO
    age: int
    statistic: PlayerShortStatisticRetrieveDTO