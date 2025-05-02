from club.models import Club
from domain.exceptions.repositories.main import RepositoryConnectionDoesNotExistError
from domain.interfaces.repositories.club.main import IClubRepository
from domain.schemas.club.main import ClubShortRetrieveDTO, ClubRetrieveDTO


class ClubRepository(IClubRepository):
    async def get_all(
            self
    ) -> list[ClubShortRetrieveDTO]:
        clubs = Club.objects.all()

        clubs_dto = [
            ClubShortRetrieveDTO.model_validate(club)
            async for club in clubs
        ]

        return clubs_dto

    async def get_club_info(
            self,
            club_id: int
    ) -> ClubRetrieveDTO:
        try:
            club = await (
                Club.objects
                .aget(id=club_id)
            )
            return ClubRetrieveDTO.model_validate(club)
        except Club.DoesNotExist:
            raise RepositoryConnectionDoesNotExistError
