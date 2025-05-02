from abc import ABC, abstractmethod

from adrf.requests import AsyncRequest


class IClubUseCase(ABC):
    @abstractmethod
    async def get_all(
            self,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    async def get_page_info(self, request: AsyncRequest, club_id: int) -> dict:
        raise NotImplementedError