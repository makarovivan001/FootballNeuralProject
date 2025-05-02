from adrf.requests import AsyncRequest

from domain.exceptions.repositories.main import RepositoryConnectionDoesNotExistError
from domain.exceptions.use_cases.common import RepositoryDoesNotExist
from domain.interfaces.repositories.club.main import IClubRepository
from domain.interfaces.repositories.game.main import IGameRepository
from domain.interfaces.repositories.player.main import IPlayerRepository
from domain.interfaces.use_cases.club.main import IClubUseCase


class ClubUseCase(IClubUseCase):
    def __init__(
            self,
            club_repository: IClubRepository,
            game_repository: IGameRepository,
            player_repository: IPlayerRepository,
    ):
        self.club_repository = club_repository
        self.game_repository = game_repository
        self.player_repository = player_repository
    async def get_all(
            self,
    ) -> dict:

        club_dto_list = await self.club_repository.get_all()

        club_list = [
            club_dto.model_dump()
            for club_dto in club_dto_list
        ]

        return {
            'clubs': club_list
        }

    async def get_page_info(
            self,
            request: AsyncRequest,
            game_id: int
    ) -> dict:
        try:
            club_dto = await self.club_repository.get_club_info(game_id)

        except RepositoryConnectionDoesNotExistError:
            raise RepositoryDoesNotExist
        club = club_dto.model_dump()

        games_dto = await self.game_repository.get_by_club_id(
            club_id=game_id,
        )

        games = [
            game.model_dump()
            for game in games_dto
        ]

        players_dto = await self.player_repository.get_by_club_id(
            club_id=game_id,
        )

        players = [
            player.model_dump()
            for player in players_dto
        ]

        return {
            "club": club,
            "games": games,
            "players": players
        }