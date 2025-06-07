from abc import ABC, abstractmethod

from domain.schemas.player.game_statistic import PlayerGameStatisticRetrieveDTO, PlayerGameStatisticShortRetrieveDTO


class IPlayerGameStatisticRepository(ABC):
    @abstractmethod
    async def get_for_game_page(
            self,
            game_id: int
    ) -> list[PlayerGameStatisticRetrieveDTO]:
        raise NotImplementedError

    @abstractmethod
    async def get_for_player_page(
            self,
            player_id: int,
            game_ids: list[int]
    ) -> list[PlayerGameStatisticShortRetrieveDTO]:
        raise NotImplementedError