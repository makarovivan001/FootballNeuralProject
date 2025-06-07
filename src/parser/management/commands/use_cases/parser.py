from application.services.common.custom_print import cprint
from domain.enums.print_colors import TextColor, BackgroundColor
from parser.management.commands.repositories.club.main import ParserClubRepository
from parser.management.commands.repositories.game.main import ParserGameRepository
from parser.management.commands.repositories.player.main import ParserPlayerRepository
from parser.management.commands.repositories.season import ParserSeasonRepository


class ParserUseCase:
    def __init__(
            self,
            season_repository: ParserSeasonRepository,
            club_repository: ParserClubRepository,
            player_repository: ParserPlayerRepository,
            game_repository: ParserGameRepository,

    ):
        cprint(f"Инжектирование зависимостей...", color=TextColor.YELLOW.value, end=' ')
        self.season_repository = season_repository
        self.club_repository = club_repository
        self.player_repository = player_repository
        self.game_repository = game_repository

        cprint(f"OK", color=TextColor.GREEN.value)

    async def start(self):
        cprint(f"Начало сбора данных...", color=TextColor.YELLOW.value)
        """
        1. Получить все сезоны
        2. Получить все матчи
        3. Получило все клубы
        4. Получить всех игроков


        :return:
        """
        seasons = await self.season_repository.get()
        club_ids = await self.season_repository.get_club_ids(seasons)
        game_ids = await self.season_repository.get_game_ids(seasons)

        clubs = await self.club_repository.get(club_ids)
        club_db_ids = await self.club_repository.create_or_update(clubs)

        players = await self.player_repository.get_from_clubs(clubs, club_db_ids)
        player_db_ids = await self.player_repository.create_or_update(players, add_statistic=True)

        games = await self.game_repository.get(game_ids)
        game_dtos = await self.game_repository.create_or_update(games, club_db_ids, player_db_ids)




    def __del__(self):
        cprint(f"Добавление/обновление данных завершено!", color=TextColor.GREEN.value)