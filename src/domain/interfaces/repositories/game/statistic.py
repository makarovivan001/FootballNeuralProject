from abc import ABC, abstractmethod

from domain.schemas.game.statistic import ClubsStatisticRetrieveDTO


class IStatisticRepository(ABC):
    @abstractmethod
    async def get_for_game(
            self,
            game_id: int,
            home_club_id: int,
            away_club_id: int,
    ) -> ClubsStatisticRetrieveDTO:
        raise NotImplementedError