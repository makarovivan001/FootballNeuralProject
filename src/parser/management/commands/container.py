from dependency_injector import containers, providers

from domain.enums.print_colors import TextColor
from parser.management.commands.enums.object_name import ObjectName
from parser.management.commands.repositories.club.main import ParserClubRepository
from parser.management.commands.repositories.game.history import ParserGameHistoryRepository
from parser.management.commands.repositories.game.main import ParserGameRepository
from parser.management.commands.repositories.game.statistic import ParserGameStatisticRepository
from parser.management.commands.repositories.game.type import ParserGameHistoryActionRepository
from parser.management.commands.repositories.player.game_statistic import ParserPlayerGameStatisticRepository
from parser.management.commands.repositories.player.injury import ParserPlayerInjuryRepository
from parser.management.commands.repositories.player.main import ParserPlayerRepository
from parser.management.commands.repositories.player.position import ParserPlayerPositionRepository
from parser.management.commands.repositories.player.role import ParserPlayerRoleRepository
from parser.management.commands.repositories.player.statistic import ParserPlayerStatisticRepository
from parser.management.commands.repositories.season import ParserSeasonRepository
from parser.management.commands.services.load_clubs import LoadClub
from parser.management.commands.services.load_data_service import LoadDataService
from parser.management.commands.services.load_game import LoadGame
from parser.management.commands.services.load_player import LoadPlayer
from parser.management.commands.services.load_seasons import LoadSeason
from parser.management.commands.use_cases.parser import ParserUseCase


class Container(containers.DeclarativeContainer):
    light_blue_color = TextColor.LIGHT_BLUE.value       # Для подсветки игроков
    light_magenta_color = TextColor.LIGHT_MAGENTA.value # Для подсветки клубов
    light_cyan_color = TextColor.LIGHT_CYAN.value       # Для подсветки игр

    user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Safari/605.1.15"
    x_mas = "eyJib2R5Ijp7InVybCI6Ii9hcGkvdGx0YWJsZT9sZWFndWVJZD02MyIsImNvZGUiOjE3NDk3MjQ0MDY3NDgsImZvbyI6InByb2R1Y3Rpb246ODYwZmI3MTdkNThmYzQ5MDI5ZDkwYmUxN2JlMzAzZWU5MGM1YTc4Yi11bmRlZmluZWQifSwic2lnbmF0dXJlIjoiREMyODE1NzlFNzUwRDA0NEEyRUI2NkMyNkExMkI1QkMifQ=="
    updating = False
    # updating = True

    season_json_path = "parser/management/commands/data/seasons/"
    game_json_path = "parser/management/commands/data/games/"
    club_json_path = "parser/management/commands/data/clubs/"
    player_json_path = "parser/management/commands/data/players/"

    load_season: LoadDataService = providers.Factory(
        LoadSeason,
        ObjectName.seasons.value,
        season_json_path,
        "https://www.fotmob.com/api/leagues?id=63&ccode3=RUS&season={obj_id}",
        user_agent,
        x_mas,
        updating,
    )
    load_game: LoadDataService = providers.Factory(
        LoadGame,
        ObjectName.games.value,
        game_json_path,
        "https://www.fotmob.com/api/matchDetails?matchId={obj_id}",
        user_agent,
        x_mas,
        updating,
    )
    load_clubs: LoadDataService = providers.Factory(
        LoadClub,
        ObjectName.clubs.value,
        club_json_path,
        "https://www.fotmob.com/api/teams?id={obj_id}&ccode3=POL",
        user_agent,
        x_mas,
        updating,
    )
    load_player: LoadDataService = providers.Factory(
        LoadPlayer,
        ObjectName.players.value,
        player_json_path,
        "https://www.fotmob.com/api/playerData?id={obj_id}",
        user_agent,
        x_mas,
        updating,
    )

    season_repository: ParserSeasonRepository = providers.Factory(
        ParserSeasonRepository,
        load_season,
        season_json_path,
    )

    club_repository: ParserClubRepository = providers.Factory(
        ParserClubRepository,
        load_clubs,
        club_json_path,
        light_magenta_color,
    )

    player_position_repository: ParserPlayerPositionRepository = providers.Factory(
        ParserPlayerPositionRepository,
    )
    player_injury_repository: ParserPlayerInjuryRepository = providers.Factory(
        ParserPlayerInjuryRepository,
    )
    player_role_repository: ParserPlayerRoleRepository = providers.Factory(
        ParserPlayerRoleRepository,
    )
    player_statistic_repository: ParserPlayerStatisticRepository = providers.Factory(
        ParserPlayerStatisticRepository,
        light_blue_color,
    )
    player_game_statistic_repository: ParserPlayerGameStatisticRepository = providers.Factory(
        ParserPlayerGameStatisticRepository,
        light_blue_color,
    )
    player_repository: ParserPlayerRepository = providers.Factory(
        ParserPlayerRepository,
        player_position_repository,
        player_injury_repository,
        player_role_repository,
        player_statistic_repository,
        load_player,
        player_json_path,
        light_blue_color,
    )

    game_statistics_repository: ParserGameStatisticRepository = providers.Factory(
        ParserGameStatisticRepository,
    )

    game_history_type_repository: ParserGameHistoryActionRepository = providers.Factory(
        ParserGameHistoryActionRepository,
    )

    game_history_repository: ParserGameHistoryRepository = providers.Factory(
        ParserGameHistoryRepository,
        game_history_type_repository,
    )

    game_repository: ParserGameRepository = providers.Factory(
        ParserGameRepository,
        player_repository,
        season_repository,
        game_statistics_repository,
        player_game_statistic_repository,
        game_history_repository,

        load_game,
        game_json_path,
        light_cyan_color,
    )

    parser_use_case: ParserUseCase = providers.Factory(
        ParserUseCase,
        season_repository,
        club_repository,
        player_repository,
        game_repository,

    )