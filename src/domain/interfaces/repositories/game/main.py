from abc import ABC, abstractmethod

from domain.schemas.game.main import GameRetrieveDTO, GameShortRetrieveDTO


class IGameRepository(ABC):
    @abstractmethod
    async def get_by_id(
            self,
            game_id: int
    ) -> GameRetrieveDTO:
        raise NotImplementedError

    @abstractmethod
    async def get_by_club_id(
            self,
            club_id: int
    ) -> list[GameShortRetrieveDTO]:
        raise NotImplementedError