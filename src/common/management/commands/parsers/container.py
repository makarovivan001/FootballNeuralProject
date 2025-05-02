from dependency_injector import containers, providers

from .get_clubs import ParserUseCase
from .repositories.interfaces.club import IClubRepositoryParser
from .repositories.interfaces.game import IGameRepositoryParser
from .repositories.interfaces.player import IPlayerRepositoryParser
from .repositories.realization.club import ClubRepositoryParser
from .repositories.realization.game import GameRepositoryParser
from .repositories.realization.player import PlayerRepositoryParser


class Container(containers.DeclarativeContainer):
    user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Safari/605.1.15"
    x_mas = "eyJib2R5Ijp7InVybCI6Ii9hcGkvbWF0Y2hEZXRhaWxzP21hdGNoSWQ9NDUxMzIzNCIsImNvZGUiOjE3NDU4NzU3MDY4MDYsImZvbyI6InByb2R1Y3Rpb246MzVmNWMyNjhjMGVjMjg2MjVhMmJlMGJkYTNhOThiZDRkODBlMzg3Zi11bmRlZmluZWQifSwic2lnbmF0dXJlIjoiMzZFQjJGQUI4NTAzMEYyNEQ4N0MzRDEyOTdGQjRGRDcifQ=="

    player_repository_parser: IPlayerRepositoryParser = providers.Factory(
        PlayerRepositoryParser,
        "https://www.fotmob.com/api/playerData?id={player_id}",
        "common/management/commands/parsers/players/",
        user_agent,
        x_mas,
    )

    club_repository_parser: IClubRepositoryParser = providers.Factory(
        ClubRepositoryParser,
        player_repository_parser,
        "https://www.fotmob.com/api/teams?id={club_id}&ccode3=POL",
        "common/management/commands/parsers/clubs/",
        user_agent,
        x_mas,
    )

    game_repository_parser: IGameRepositoryParser = providers.Factory(
        GameRepositoryParser,
        player_repository_parser,
        club_repository_parser,
        "https://www.fotmob.com/api/matchDetails?matchId={game_id}",
        "common/management/commands/parsers/games/",
        "common/management/commands/parsers/seasons/",
        user_agent,
        x_mas,
    )

    parser_use_case: ParserUseCase = providers.Factory(
        ParserUseCase,
        club_repository_parser,
        game_repository_parser,
        "https://www.fotmob.com/api/leagues?id=63&ccode3=RUS&season={season}",
        "common/management/commands/parsers/",
        user_agent,
        x_mas
    #     https://www.fotmob.com/api/leagues?id=63&ccode3=RUS&season=2012%2F2013
    #                                                                     /
    )


parser_container = Container()