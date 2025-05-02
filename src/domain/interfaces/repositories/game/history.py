from abc import ABC, abstractmethod

from domain.schemas.game.history import HistoryRetrieveDTO


class IHistoryRepository(ABC):
    @abstractmethod
    async def get_for_game(
            self,
            game_id: int,
    ) -> list[HistoryRetrieveDTO]:
        raise NotImplementedError