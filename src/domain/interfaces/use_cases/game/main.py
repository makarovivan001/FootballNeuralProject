from abc import ABC, abstractmethod

from adrf.requests import AsyncRequest


class IGameUseCase(ABC):
    @abstractmethod
    async def get_page_info(self, request: AsyncRequest, game_id: int) -> dict:
        raise NotImplementedError