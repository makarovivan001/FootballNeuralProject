from abc import ABC, abstractmethod

from django.db.models import F

from domain.exceptions.repositories.main import RepositoryConnectionDoesNotExistError
from domain.interfaces.repositories.player.statistic import IStatisticRepository
from domain.schemas.player.statistic import PlayerStatisticRetrieveDTO
from player.models import PlayerStatistic


class StatisticRepository(IStatisticRepository):
    async def get_by_player_id(
            self,
            player_id: int
    ) -> PlayerStatisticRetrieveDTO:
        try:
            stats = await (
                PlayerStatistic.objects
                .aget(player__id=player_id)
            )
            return PlayerStatisticRetrieveDTO.model_validate(stats)
        except PlayerStatistic.DoesNotExist:
            raise RepositoryConnectionDoesNotExistError

    async def get_by_player_ids(
            self,
            player_ids: list[int]
    ) -> list[PlayerStatisticRetrieveDTO]:
        statistics = PlayerStatistic.objects.filter(
            player__id__in=player_ids
        ).annotate(
            player_id=F('player__id')
        )

        return [
            PlayerStatisticRetrieveDTO.model_validate(statistic)
            async for statistic in statistics
        ]
