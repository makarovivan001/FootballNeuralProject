from domain.interfaces.repositories.game.statistic import IStatisticRepository
from domain.schemas.game.statistic import ClubsStatisticRetrieveDTO, StatisticRetrieveDTO
from game.models import GameStatistic


class StatisticRepository(IStatisticRepository):
    async def get_for_game(
            self,
            game_id: int,
            home_club_id: int,
            away_club_id: int,
    ) -> ClubsStatisticRetrieveDTO:

        statistics = GameStatistic.objects.filter(
            game_id=game_id
        )

        try:
            home_club_statistic = await statistics.aget(
                club_id=home_club_id
            )
        except GameStatistic.DoesNotExist:
            home_club_statistic = None

        try:
            away_club_statistic = await statistics.aget(
                club_id=away_club_id
            )
        except GameStatistic.DoesNotExist:
            away_club_statistic = None

        if home_club_statistic:
            home_club_statistic_dto = StatisticRetrieveDTO.model_validate(home_club_statistic)
        else:
            home_club_statistic_dto = None

        if away_club_statistic:
            away_club_statistic_dto = StatisticRetrieveDTO.model_validate(away_club_statistic)
        else:
            away_club_statistic_dto = None

        return ClubsStatisticRetrieveDTO(
            home_club_statistic=home_club_statistic_dto,
            away_club_statistic=away_club_statistic_dto,
        )