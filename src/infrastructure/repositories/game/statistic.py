from domain.interfaces.repositories.game.statistic import IStatisticRepository
from domain.schemas.game.statistic import ClubsStatisticRetrieveDTO, StatisticRetrieveDTO
from game.models import Statistic


class StatisticRepository(IStatisticRepository):
    async def get_for_game(
            self,
            game_id: int,
            home_club_id: int,
            away_club_id: int,
    ) -> ClubsStatisticRetrieveDTO:

        statistics = Statistic.objects.filter(
            game_id=game_id
        )
        home_club_statistic = await statistics.aget(
            club_id=home_club_id
        )
        away_club_statistic = await statistics.aget(
            club_id=away_club_id
        )

        home_club_statistic_dto = StatisticRetrieveDTO.model_validate(home_club_statistic)
        away_club_statistic_dto = StatisticRetrieveDTO.model_validate(away_club_statistic)

        return ClubsStatisticRetrieveDTO(
            home_club_statistic=home_club_statistic_dto,
            away_club_statistic=away_club_statistic_dto,
        )