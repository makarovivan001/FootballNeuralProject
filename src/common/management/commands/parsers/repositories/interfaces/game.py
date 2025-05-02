from abc import ABC, abstractmethod


class IGameRepositoryParser(ABC):
    @abstractmethod
    def get_seasons(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_match_info(self, match_id: int) -> None:
        raise NotImplementedError