from dependency_injector import containers, providers

from application.use_cases.club.main import ClubUseCase
from domain.interfaces.repositories.club.main import IClubRepository
from domain.interfaces.use_cases.club.main import IClubUseCase
from infrastructure.repositories.club.main import ClubRepository

from player.container import Container as PlayerContainer, container as player_container
from game.container import Container as GameContainer, container as game_container
from season.container import Container as SeasonContainer, container as season_container


class Container(containers.DeclarativeContainer):
    player_container: PlayerContainer = providers.Container(PlayerContainer)
    game_container: GameContainer = providers.Container(GameContainer)
    season_container: SeasonContainer = providers.Container(SeasonContainer)

    club_repository: IClubRepository = providers.Factory(
        ClubRepository,
    )

    club_use_case: IClubUseCase = providers.Factory(
        ClubUseCase,
        club_repository,
        game_container.game_repository,
        player_container.player_repository,
        season_container.season_repository,
    )


container = Container(
    player_container=player_container,
    game_container=game_container,
    season_container=season_container,
)