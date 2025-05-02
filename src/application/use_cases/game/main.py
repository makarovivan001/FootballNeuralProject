from adrf.requests import AsyncRequest

from domain.exceptions.repositories.main import RepositoryConnectionDoesNotExistError
from domain.exceptions.use_cases.common import RepositoryDoesNotExist
from domain.interfaces.repositories.game.history import IHistoryRepository
from domain.interfaces.repositories.game.main import IGameRepository
from domain.interfaces.repositories.game.statistic import IStatisticRepository
from domain.interfaces.use_cases.game.main import IGameUseCase


class GameUseCase(IGameUseCase):
    def __init__(
            self,
            game_repository: IGameRepository,
            statistic_repository: IStatisticRepository,
            history_repository: IHistoryRepository,
    ):
        self.game_repository = game_repository
        self.statistic_repository = statistic_repository
        self.history_repository = history_repository

    async def get_page_info(
            self, request: AsyncRequest, game_id: int
    ) -> dict:
        try:
            game_dto = await self.game_repository.get_by_id(game_id)

        except RepositoryConnectionDoesNotExistError:
            raise RepositoryDoesNotExist

        statistics_dto = await self.statistic_repository.get_for_game(
            game_id=game_id,
            home_club_id=game_dto.home_club.id,
            away_club_id=game_dto.away_club.id,
        )

        histories_dto = await self.history_repository.get_for_game(
            game_id=game_id,
        )

        histories = [
            history.model_dump()
            for history in histories_dto
        ]

        statistics = statistics_dto.model_dump()
        game = game_dto.model_dump()

        return {
            'game': game,
            'statistics': statistics,
            'histories': histories,
        }