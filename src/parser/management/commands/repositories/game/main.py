from asgiref.sync import sync_to_async
from django.conf import settings
from pydantic import ValidationError

from application.services.common.custom_print import cprint
from domain.enums.print_colors import TextColor
from game.models import Game
from parser.management.commands.exceptions.main import GetPlayersToCreateError
from parser.management.commands.repositories.game.history import ParserGameHistoryRepository
from parser.management.commands.repositories.game.statistic import ParserGameStatisticRepository
from parser.management.commands.repositories.player.game_statistic import ParserPlayerGameStatisticRepository
from parser.management.commands.repositories.player.main import ParserPlayerRepository
from parser.management.commands.repositories.season import ParserSeasonRepository
from parser.management.commands.schemas.game.main import ParserGameCreateDTO, ParserGameUpdateDTO, \
    ParserGameShortRetrieveDTO
from parser.management.commands.services.load_data_service import LoadDataService


class ParserGameRepository:
    def __init__(
        self,
        player_repository: ParserPlayerRepository,
        season_repository: ParserSeasonRepository,
        game_statistics_repository: ParserGameStatisticRepository,
        player_game_statistic_repository: ParserPlayerGameStatisticRepository,
        game_history_repository: ParserGameHistoryRepository,

        load_game: LoadDataService,
        dir_url,
        light_cyan_color,
    ):
        self.player_repository = player_repository
        self.season_repository = season_repository
        self.game_statistics_repository = game_statistics_repository
        self.player_game_statistic_repository = player_game_statistic_repository
        self.game_history_repository = game_history_repository

        self.load_game = load_game
        self.dir_url = settings.BASE_DIR / dir_url
        self.light_cyan_color = light_cyan_color

    async def get(self, game_ids: dict) -> dict:
        game_of_seasons = {}
        for key, value in game_ids.items():
            games = await sync_to_async(self.load_game.get_data)(value)

            for game in games:
                if game is None:
                    games.remove(game)

            game_of_seasons[key] = games

        return game_of_seasons

    async def create_or_update(self, games_of_seasons: dict, club_db_ids: dict, player_db_ids: dict) -> dict[int, ParserGameShortRetrieveDTO]:
        cprint("Начало созданя/обновления игр...", color=TextColor.YELLOW.value)
        for_update = []
        for_create = []

        for season, games in games_of_seasons.items():
            season_id = await self.season_repository.get_or_create(season)

            for game_data in games:
                if game_data.get('error', False):
                    continue

                cprint(f"Начало сбора данных для игры - {game_data['general']['matchId']})", color=self.light_cyan_color, end=" -> ")

                try:
                    home_club_placement, home_participating_player_ids = await self.__make_club_placement(game_data, 'homeTeam', player_db_ids)
                    away_club_placement, away_participating_player_ids = await self.__make_club_placement(game_data, 'awayTeam', player_db_ids)
                except GetPlayersToCreateError:
                    continue

                try:
                    game_data.update({
                        "home_club_placement": home_club_placement,
                        "away_club_placement": away_club_placement,
                        "home_players": home_participating_player_ids,
                        "away_players": away_participating_player_ids,
                        "home_club_id": club_db_ids[game_data['general']['homeTeam']['id']],
                        "away_club_id": club_db_ids[game_data['general']['awayTeam']['id']],
                        "tour": game_data['general']['matchRound'],
                        "season_id": season_id,
                    })

                    game_create_dto = ParserGameCreateDTO(
                        **game_data
                    )
                except KeyError:
                    continue
                except ValidationError as exc:
                    print(exc)

                cprint(f"Данные собраны!", color=TextColor.GREEN.value)
                try:
                    game = await Game.objects.aget(identifier=game_create_dto.identifier)
                    try:
                        game_update_dto = ParserGameUpdateDTO(id=game.id, **game_data)
                    except ValidationError as exc:
                        print(exc)
                    for_update.append(
                        Game(**game_update_dto.model_dump())
                    )
                    cprint(f"Добавлено на обновление", color=TextColor.GREEN.value)
                except Game.DoesNotExist:
                    for_create.append(
                        Game(**game_create_dto.model_dump())
                    )
                    cprint(f"Добавлено на создание", color=TextColor.GREEN.value)

        if len(for_update) != 0:
            await self.__update_games(for_update)

        if len(for_create) != 0:
            await self.__create_games(for_create)

        game_dtos = await self.get_dtos()
        await self.game_statistics_repository.create_or_update(games_of_seasons, game_dtos)
        await self.player_game_statistic_repository.create_or_update(games_of_seasons, game_dtos, player_db_ids)
        await self.game_history_repository.create_or_update(games_of_seasons, game_dtos, player_db_ids)

        return game_dtos

    async def __create_games(self, games: list[Game]) -> None:
        cprint(f"Создание клубов...", color=TextColor.YELLOW.value, end=" ")
        await Game.objects.abulk_create(
            games,
            batch_size=1000
        )
        cprint(f"OK", color=TextColor.GREEN.value)

    async def __update_games(self, games: list[Game]) -> None:
        cprint(f"Обновление клубов...", color=TextColor.YELLOW.value, end=" ")
        await Game.objects.abulk_update(
            games,
            batch_size=1000,
            fields=[
                "is_finished",
                "home_club",
                "away_club",
                "best_player",
                "home_score",
                "away_score",
                "home_club_placement",
                "away_club_placement",
                "home_players",
                "away_players",
                "season_id",
            ]
        )
        cprint(f"OK", color=TextColor.GREEN.value)

    async def __make_club_placement(self, game: dict, club_position: str, player_db_ids: dict) -> (list, list[int]):
        try:
            club_formation: str = game['content']['lineup'][club_position]['formation']
        except KeyError:
            return [], []
        except TypeError:
            return [], []

        if not game['general']['started']:
            cprint(f"Матча не было. Данных нет!", color=TextColor.RED.value)
            return [], []

        club_player_starters: dict = game['content']['lineup'][club_position]

        club_players_in_game = club_player_starters['starters'] + club_player_starters['subs']

        try:
            players_to_create = []
            for player_id in club_players_in_game:
                if not player_db_ids.get(player_id['id'], False):
                    players_to_create.append(player_id['id'])
        except KeyError:
            raise GetPlayersToCreateError

        if len(players_to_create) != 0:
            cprint(f"Некоторых игроков нет в БД. Создание...", color=TextColor.RED.value)
            new_players = await self.player_repository.get(players_to_create)
            created_player_db_ids = await self.player_repository.create_or_update(new_players, add_statistic=True)

            player_db_ids = created_player_db_ids.copy()
            del new_players
            del created_player_db_ids
            cprint(f"Новые юзеры добавлены!", color=TextColor.GREEN.value)

        participating_player_ids = []
        for player_id in club_players_in_game:
            if player_db_ids.get(player_id['id'], False):
                participating_player_ids.append(player_db_ids[player_id['id']])
            else:
                cprint(f"Игрока {player_id['id']} нет. Создание...", color=TextColor.RED.value)
                new_player = await self.player_repository.get([player_id['id']])
                created_player_db_ids = await self.player_repository.create_or_update(new_player, add_statistic=True)
                player_db_ids = created_player_db_ids.copy()
                del new_player
                del created_player_db_ids

        goalkeeper: dict = club_player_starters['starters'].pop(0)

        try:
            club_placement = [
                [{
                    'id': player_db_ids[goalkeeper['id']],
                    'position_id': goalkeeper['positionId']
                }]
            ]
        except KeyError:
            club_placement = [
                [{
                    'id': None,
                    'position_id': goalkeeper['positionId']
                }]
            ]

        index = 0
        for count_on_position in list(map(int, club_formation.split('-'))):
            club_placement.append([])
            for _ in range(count_on_position):
                try:
                    club_placement[-1].append({
                        'id': player_db_ids[club_player_starters['starters'][index]['id']],
                        'position_id': club_player_starters['starters'][index]['positionId']
                    })
                except KeyError:
                    club_placement[-1].append({
                        'id': None,
                        'position_id': club_player_starters['starters'][index]['positionId']
                    })
                except IndexError as exc:
                    club_placement[-1].append({
                        'id': None,
                        'position_id': None
                    })

                index += 1

        return club_placement, participating_player_ids

    async def get_db_ids(self) -> dict:
        cprint(f"Получение словаря с identifier: id ...", color=self.light_cyan_color, end=" ")
        game_db_ids = {
            game.identifier: game.id
            async for game in Game.objects.all()
        }

        cprint(f"OK", color=TextColor.GREEN.value)
        return game_db_ids

    async def get_dtos(self) -> dict[int, ParserGameShortRetrieveDTO]:
        cprint(f"Получение DTO с identifier: id ...", color=self.light_cyan_color, end=" ")
        game_dtos = {
            game.identifier: ParserGameShortRetrieveDTO.model_validate(game)
            async for game in Game.objects.all()
        }

        cprint(f"OK", color=TextColor.GREEN.value)
        return game_dtos