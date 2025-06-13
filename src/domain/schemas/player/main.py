from decimal import Decimal

from django.db.models.fields.files import ImageFieldFile
from pydantic import BaseModel, field_validator

from domain.schemas.club.main import ClubShortRetrieveDTO
from domain.schemas.player.position import PlayerPositionRetrieveDTO
from domain.schemas.player.statistic import PlayerShortStatisticRetrieveDTO, PlayerStatisticRetrieveDTO


class PlayerShortRetrieveDTO(BaseModel):
    id: int
    photo: str
    photo_url: str | None
    surname: str
    name: str
    number: int | None
    actions: list = []
    primary_position: PlayerPositionRetrieveDTO | None = None

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
    photo_url: str | None
    club: ClubShortRetrieveDTO
    age: int
    statistic: PlayerShortStatisticRetrieveDTO | None
    number: int | None


    class Config:
        from_attributes = True


class PlayerRetrieveDTO(PlayerShortRetrieveDTO):
    country: str
    age: int
    club: ClubShortRetrieveDTO | None
    primary_position: PlayerPositionRetrieveDTO | None = None

class PlayerAllStatsRetrieveDTO(BaseModel):
    id: int
    surname: str
    name: str
    photo_url: str | None
    club: ClubShortRetrieveDTO | None
    age: int
    statistic: PlayerStatisticRetrieveDTO | None
    number: int | None
    primary_position: PlayerPositionRetrieveDTO | None = None


    class Config:
        from_attributes = True