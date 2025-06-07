from abc import ABC, abstractmethod

from domain.schemas.player.statistic import PlayerStatisticRetrieveDTO


class IStatisticRepository(ABC):
    @abstractmethod
    async def get_by_player_id(
            self,
            player_id: int
    ) -> PlayerStatisticRetrieveDTO:
        raise NotImplementedError

    @abstractmethod
    async def get_by_player_ids(
            self,
            player_ids: list[int]
    ) -> list[PlayerStatisticRetrieveDTO]:
        raise NotImplementedError