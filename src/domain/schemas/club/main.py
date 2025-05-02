from django.db.models.fields.files import ImageFieldFile
from pydantic import BaseModel, field_validator


class ClubShortRetrieveDTO(BaseModel):
    id: int
    name: str
    photo: str | None
    photo_url: str | None

    class Config:
        from_attributes = True

    @field_validator('photo', mode="before")
    @staticmethod
    def image_validator(image: ImageFieldFile | None) -> str:
        if image:
            return image.url
        return ""

class ClubRetrieveDTO(ClubShortRetrieveDTO):
    stadium_name: str
    stadium_count_of_sits: int
    city_name: str