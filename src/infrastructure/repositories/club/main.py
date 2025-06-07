from django.db.models import Case, When, Q

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

    async def get_by_season_id(
            self,
            last_season_id
    ) -> list[ClubShortRetrieveDTO]:
        clubs = Club.objects.filter(
            Q(away_club__season_id=last_season_id) |
            Q(home_club__season_id=last_season_id)
        ).distinct()

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

    async def get_sorted_clubs(self, sorted_ids: list[int]) -> dict[int, ClubShortRetrieveDTO]:

        clubs = Club.objects.filter(id__in=sorted_ids).order_by(
            Case(*[When(id=club_id, then=index) for index, club_id in enumerate(sorted_ids, 1)])
        )

        return {
            club.id: ClubShortRetrieveDTO.model_validate(club)
            async for club in clubs
        }