from dependency_injector import containers, providers

from application.use_cases.game.main import GameUseCase
from domain.interfaces.repositories.game.history import IHistoryRepository
from domain.interfaces.repositories.game.main import IGameRepository
from domain.interfaces.repositories.game.statistic import IStatisticRepository
from domain.interfaces.repositories.player.game_statistic import IPlayerGameStatisticRepository
from domain.interfaces.repositories.player.main import IPlayerRepository
from domain.interfaces.use_cases.game.main import IGameUseCase
from infrastructure.repositories.game.history import HistoryRepository
from infrastructure.repositories.game.main import GameRepository
from infrastructure.repositories.game.statistic import StatisticRepository
from infrastructure.repositories.player.game_statistic import PlayerGameStatisticRepository
from infrastructure.repositories.player.main import PlayerRepository


class Container(containers.DeclarativeContainer):
    player_repository: IPlayerRepository = providers.Factory(
        PlayerRepository,
    )
    player_game_statistic_repository: IPlayerGameStatisticRepository = providers.Factory(
        PlayerGameStatisticRepository,
    )
    game_repository: IGameRepository = providers.Factory(
        GameRepository
    )

    statistic_repository: IStatisticRepository = providers.Factory(
        StatisticRepository
    )
    history_repository: IHistoryRepository = providers.Factory(
        HistoryRepository
    )

    game_use_case: IGameUseCase = providers.Factory(
        GameUseCase,
        game_repository,
        statistic_repository,
        history_repository,
        player_repository,
        player_game_statistic_repository
    )


container = Container()