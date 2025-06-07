from abc import ABC, abstractmethod

from django.db.models import Q
from pydantic import BaseModel

from domain.schemas.game.main import GameShortRetrieveDTO
from domain.schemas.player.main import PlayerStatsRetrieveDTO, PlayerRetrieveDTO, PlayerShortRetrieveDTO, \
    PlayerAllStatsRetrieveDTO


class IPlayerRepository(ABC):
    @abstractmethod
    async def get_by_club_id(
            self,
            club_id: int,
            dto_model: BaseModel = PlayerStatsRetrieveDTO,
            param: Q = Q(),
    ) -> list[PlayerStatsRetrieveDTO]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(
            self,
            player_id: int
    ) -> PlayerRetrieveDTO:
        raise NotImplementedError

    @abstractmethod
    async def get_by_ids(
            self,
            player_ids: list[int],
            dto_model: BaseModel = PlayerAllStatsRetrieveDTO,
    ) -> dict[int, PlayerShortRetrieveDTO | PlayerAllStatsRetrieveDTO]:
        raise NotImplementedError

    @abstractmethod
    async def get_all(
            self
    ) -> list[PlayerAllStatsRetrieveDTO]:
        raise NotImplementedError
