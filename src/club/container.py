from dependency_injector import containers, providers

from application.use_cases.club.main import ClubUseCase
from domain.interfaces.repositories.club.main import IClubRepository
from domain.interfaces.repositories.game.main import IGameRepository
from domain.interfaces.repositories.player.main import IPlayerRepository
from domain.interfaces.use_cases.club.main import IClubUseCase
from infrastructure.repositories.club.main import ClubRepository
from infrastructure.repositories.game.main import GameRepository
from infrastructure.repositories.player.main import PlayerRepository


class Container(containers.DeclarativeContainer):
    club_repository: IClubRepository = providers.Factory(
        ClubRepository,
    )

    game_repository: IGameRepository = providers.Factory(
        GameRepository,
    )

    player_repository: IPlayerRepository = providers.Factory(
        PlayerRepository,
    )

    club_use_case: IClubUseCase = providers.Factory(
        ClubUseCase,
        club_repository,
        game_repository,
        player_repository
    )


container = Container()