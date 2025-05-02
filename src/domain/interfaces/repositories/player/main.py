from abc import ABC, abstractmethod

from domain.schemas.game.main import GameShortRetrieveDTO
from domain.schemas.player.main import PlayerStatsRetrieveDTO


class IPlayerRepository(ABC):
    @abstractmethod
    async def get_by_club_id(
            self,
            club_id: int
    ) -> list[PlayerStatsRetrieveDTO]:
        raise NotImplementedError