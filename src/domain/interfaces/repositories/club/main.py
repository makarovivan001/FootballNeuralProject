from abc import ABC, abstractmethod

from domain.schemas.club.main import ClubShortRetrieveDTO, ClubRetrieveDTO


class IClubRepository(ABC):
    @abstractmethod
    async def get_all(
            self
    ) -> list[ClubShortRetrieveDTO]:
        raise NotImplementedError

    @abstractmethod
    async def get_club_info(
            self,
            club_id: int
    ) -> ClubRetrieveDTO:
        raise NotImplementedError

    @abstractmethod
    async def get_sorted_clubs(
            self,
            sorted_ids: list[int]
    ) -> dict[int, ClubShortRetrieveDTO]:
        raise NotImplemented


