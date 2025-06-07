from dependency_injector import containers, providers

from application.use_cases.player.main import PlayerUseCase
from domain.interfaces.repositories.player.game_statistic import IPlayerGameStatisticRepository
from domain.interfaces.repositories.player.main import IPlayerRepository
from domain.interfaces.repositories.player.statistic import IStatisticRepository
from domain.interfaces.use_cases.player.main import IPlayerUseCase
from infrastructure.repositories.player.game_statistic import PlayerGameStatisticRepository
from infrastructure.repositories.player.main import PlayerRepository

from game.container import Container as GameContainer, container as game_container
from infrastructure.repositories.player.statistic import StatisticRepository


class Container(containers.DeclarativeContainer):
    game_container: GameContainer = providers.Container(GameContainer)

    player_repository: IPlayerRepository = providers.Factory(
        PlayerRepository,
    )

    statistic_repository: IStatisticRepository = providers.Factory(
        StatisticRepository,
    )

    player_game_statistic_repository: IPlayerGameStatisticRepository = providers.Factory(
        PlayerGameStatisticRepository,
    )

    player_use_case: IPlayerUseCase = providers.Factory(
        PlayerUseCase,
        player_repository,
        game_container.game_repository,
        statistic_repository,
        player_game_statistic_repository
    )

container = Container(
    game_container=game_container,
)