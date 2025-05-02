from abc import ABC, abstractmethod


class IClubRepositoryParser(ABC):
    @abstractmethod
    def get_clubs(self, club_ids: set[int]) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_by_identifier(self, identifiers: list[int]) -> dict:
        raise NotImplementedError