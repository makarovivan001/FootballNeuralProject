from abc import ABC, abstractmethod


class IPlayerRepositoryParser(ABC):
    @abstractmethod
    def create_for_club(self, squad: list[dict], club_id_dto) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_by_identifier(self, identifiers: list[dict]) -> dict:
        raise NotImplementedError