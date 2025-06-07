from domain.interfaces.repositories.season.main import ISeasonRepository
from season.models import Season


class SeasonRepository(ISeasonRepository):
    async def get_last(self) -> int:
        season = await Season.objects.afirst()

        return season.id

    async def get_all_ids(self) -> list[int]:
        seasons = Season.objects.all()

        season_ids = [
            season.id
            async for season in seasons
        ]

        return season_ids