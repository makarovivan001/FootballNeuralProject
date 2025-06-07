from django.db.models import Q

from application.services.common.custom_print import cprint
from domain.enums.print_colors import TextColor
from game.models import GameStatistic
from parser.management.commands.exceptions.main import GameNotFinishError, GameStatisticDoesNotExistError
from parser.management.commands.schemas.game.main import ParserGameShortRetrieveDTO
from parser.management.commands.schemas.game.statistic import ParserGameStatisticUpdateDTO, ParserGameStatisticCreateDTO


class ParserGameStatisticRepository:
    def __init__(
        self
    ) -> None:
        ...

    async def create_or_update(self, games_of_seasons: dict, game_dtos: dict[int, ParserGameShortRetrieveDTO]) -> int | None:
        for_update = []
        for_create = []
        cprint(f"Попытка добавления статистики для матчей...", color=TextColor.YELLOW.value)

        for season, games in games_of_seasons.items():
            for game_data in games:
                try:
                    try:
                        game: ParserGameShortRetrieveDTO = game_dtos[int(game_data['general']['matchId'])]
                    except KeyError:
                        raise Exception

                    if not game.is_finished:
                        raise GameNotFinishError

                    home_statistic_data = {
                        "club_id": game.home_club_id,
                        "game_id": game.id,
                    }
                    away_statistic_data = {
                        "club_id": game.away_club_id,
                        "game_id": game.id,
                    }
                    try:
                        game_statistic: list = game_data['content']['stats']['Periods']['All']['stats']
                    except KeyError:
                        raise GameStatisticDoesNotExistError
                    except TypeError:
                        raise GameStatisticDoesNotExistError

                    for stat_block in game_statistic:
                        for statistic in stat_block["stats"]:
                            if statistic['stats'][0] is None:
                                continue

                            if isinstance(statistic['stats'][0], str) and "%" in statistic['stats'][0]:
                                home_stats = statistic['stats'][0].split()
                                home_value = int(home_stats[0])
                                home_persent = int(home_stats[1].strip('()%'))

                                away_stats = statistic['stats'][1].split()
                                away_value = int(away_stats[0])
                                away_persent = int(away_stats[1].strip('()%'))

                                home_statistic_data[statistic['key']] = home_value
                                away_statistic_data[statistic['key']] = away_value

                                home_statistic_data[statistic['key'] + "_persent"] = home_persent
                                away_statistic_data[statistic['key'] + "_persent"] = away_persent
                            else:
                                home_statistic_data[statistic['key']] = statistic['stats'][0]
                                away_statistic_data[statistic['key']] = statistic['stats'][1]

                    try:
                        home_game_statistic = await GameStatistic.objects.aget(game_id=game.id, club_id=game.home_club_id)
                        away_game_statistic = await GameStatistic.objects.aget(game_id=game.id, club_id=game.away_club_id)
                        home_game_statistic_update_dto = ParserGameStatisticUpdateDTO(id=home_game_statistic.id, **home_statistic_data)
                        away_game_statistic_update_dto = ParserGameStatisticUpdateDTO(id=away_game_statistic.id, **away_statistic_data)

                        for_update.append(GameStatistic(**home_game_statistic_update_dto.model_dump()))
                        for_update.append(GameStatistic(**away_game_statistic_update_dto.model_dump()))
                    except GameStatistic.DoesNotExist as exc:
                        home_game_statistic_update_dto = ParserGameStatisticCreateDTO(**home_statistic_data)
                        away_game_statistic_update_dto = ParserGameStatisticCreateDTO(**away_statistic_data)

                        for_create.append(GameStatistic(**home_game_statistic_update_dto.model_dump()))
                        for_create.append(GameStatistic(**away_game_statistic_update_dto.model_dump()))

                except KeyError:
                    cprint(f"Почему-то нет матча с ID = {game_data['general']['matchId']}", color=TextColor.RED.value)
                except GameNotFinishError:
                    cprint(f"Игры с ID = {game_data['general']['matchId']} ещё не было", color=TextColor.RED.value)
                except GameStatisticDoesNotExistError:
                    cprint(f"Для игры с ID = {game_data['general']['matchId']} нет статистики", color=TextColor.RED.value)
                except Exception as exc:
                    cprint(f"Ничего нет...", color=TextColor.RED.value)

        if len(for_update) != 0:
            await self.__update_game_statistic(for_update)
        if len(for_create) != 0:
            await self.__create_game_statistic(for_create)
        else:
            cprint(f"Нет статистики", color=TextColor.RED.value)


    async def __create_game_statistic(self, game_statistic_create_dto: list[GameStatistic]) -> None:
        cprint(f"Создание статистики...", color=TextColor.YELLOW.value, end=" ")
        await GameStatistic.objects.abulk_create(
            game_statistic_create_dto,
            batch_size=1000
        )
        cprint(f"OK", color=TextColor.GREEN.value)

    async def __update_game_statistic(self, game_statistic_update_dto: list[GameStatistic]) -> None:
        cprint(f"Обновление статистики...", color=TextColor.YELLOW.value, end=" ")
        await GameStatistic.objects.abulk_update(
            game_statistic_update_dto,
            batch_size=1000,
            fields=[
                "big_chance",
                "big_chance_missed_title",
                "fouls",
                "corners",
                "total_shots",
                "shots_on_target",
                "shots_off_target",
                "blocked_shots",
                "shots_woodwork",
                "shots_inside_box",
                "shots_outside_box",
                "passes",
                "accurate_passes",
                "accurate_passes_persent",
                "own_half_passes",
                "opposition_half_passes",
                "long_balls_accurate",
                "long_balls_accurate_persent",
                "accurate_crosses",
                "accurate_crosses_persent",
                "player_throws",
                "touches_opp_box",
                "offsides",
                "tackles_succeeded",
                "tackles_succeeded_persent",
                "interceptions",
                "shot_blocks",
                "clearances",
                "keeper_saves",
                "duel_won",
                "ground_duels_won",
                "ground_duels_won_persent",
                "aerials_won",
                "aerials_won_persent",
                "dribbles_succeeded",
                "dribbles_succeeded_persent",
                "yellow_cards",
                "red_cards",
            ]
        )
        cprint(f"OK", color=TextColor.GREEN.value)