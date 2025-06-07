from abc import ABC, abstractmethod


class ISeasonRepository(ABC):
    @abstractmethod
    async def get_last(self) -> int:
        raise NotImplementedError

    @abstractmethod
    async def get_all_ids(self) -> list[int]:
        raise NotImplementedError