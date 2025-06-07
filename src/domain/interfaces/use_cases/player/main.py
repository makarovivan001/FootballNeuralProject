from abc import ABC, abstractmethod


class IPlayerUseCase(ABC):
    @abstractmethod
    async def get_info(
            self,
            player_id: int,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    async def get_best_positions(self, player_id: int) -> list[tuple[str, float]]:
        raise NotImplementedError

