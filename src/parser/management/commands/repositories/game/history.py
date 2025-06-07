from application.services.common.custom_print import cprint
from domain.enums.print_colors import TextColor
from game.models import History
from parser.management.commands.exceptions.main import GameNotFinishError, GameHistoryDoesNotExistError
from parser.management.commands.repositories.game.type import ParserGameHistoryActionRepository
from parser.management.commands.schemas.game.history import HistoryCreateDTO
from parser.management.commands.schemas.game.main import ParserGameShortRetrieveDTO


class ParserGameHistoryRepository:
    def __init__(
            self,
            game_history_action_repository: ParserGameHistoryActionRepository
    ) -> None:
        self.game_history_action_repository = game_history_action_repository

    async def create_or_update(self, games_of_seasons: dict, game_dtos: dict[int, ParserGameShortRetrieveDTO], player_db_ids: dict) -> int | None:
        for_create = []
        cprint(f"Попытка добавления истории для матчей...", color=TextColor.YELLOW.value)

        await self.__delete_game_statistics()
        for season, games in games_of_seasons.items():
            for game_data in games:
                try:
                    try:
                        game: ParserGameShortRetrieveDTO = game_dtos[int(game_data['general']['matchId'])]
                    except KeyError:
                        raise Exception

                    if not game.is_finished:
                        raise GameNotFinishError

                    try:
                        game_history: list = game_data['content']['matchFacts']['events']['events']
                    except KeyError as exc:
                        raise GameHistoryDoesNotExistError
                    except TypeError as exc:
                        raise GameHistoryDoesNotExistError

                    for history in game_history:
                        type_name = history['type']
                        if type_name:
                            type_name = history.get('card', history['type'])

                        action_id = await self.game_history_action_repository.get_or_create(type_name)

                        try:
                            swap = None
                            player_id = None
                            if history['player']['id'] is None:
                                if history['type'] == 'Substitution':
                                    swap = []
                                    swap.append(player_db_ids[int(history['swap'][0]['id'])])
                                    swap.append(player_db_ids[int(history['swap'][1]['id'])])
                            else:
                                player_id = player_db_ids[history['player']['id']]
                        except Exception as exc:
                            ...

                        try:
                            history_dto = HistoryCreateDTO(**{
                                "game_id": game.id,
                                "player_id": player_id,
                                "action_id": action_id,
                                "swap": swap,
                                "is_home": history['isHome'],
                                "minutes": history['time'],
                                "overload_minutes": history['overloadTime'],
                            })
                            history_obj = History(**history_dto.model_dump())
                            for_create.append(history_obj)
                        except Exception as exc:
                            ...

                    if len(for_create) != 0:
                        await self.__create_game_statistic(for_create)
                        for_create = []

                except KeyError as exc:
                    cprint(f"Почему-то нет матча с ID = {game_data['general']['matchId']}", color=TextColor.RED.value)
                except GameNotFinishError:
                    cprint(f"Игры с ID = {game_data['general']['matchId']} ещё не было", color=TextColor.RED.value)
                except GameHistoryDoesNotExistError:
                    cprint(f"Для игры с ID = {game_data['general']['matchId']} нет истории", color=TextColor.RED.value)
                except Exception:
                    cprint(f"Ничего нет...", color=TextColor.RED.value)

    async def __delete_game_statistics(self) -> None:
        cprint(f"Удаление всей истории...", color=TextColor.YELLOW.value, end=" ")
        try:
            await History.objects.all().adelete()
        except Exception as exc:
            cprint(f"Ошибка удаления", color=TextColor.RED.value)
        cprint(f"OK", color=TextColor.GREEN.value)

    async def __create_game_statistic(self, game_history_create_dto: list[History]) -> None:
        cprint(f"Создание истории...", color=TextColor.YELLOW.value, end=" ")
        try:
            await History.objects.abulk_create(
                game_history_create_dto,
                batch_size=1000
            )
        except Exception as exc:
            cprint(f"Ошибка создания", color=TextColor.RED.value)
        cprint(f"OK", color=TextColor.GREEN.value)

    async def __update_game_statistic(self, game_history_update_dto: list[History]) -> None:
        cprint(f"Обновление истории...", color=TextColor.YELLOW.value, end=" ")
        await History.objects.abulk_update(
            game_history_update_dto,
            batch_size=1000,
            fields=[
                "game_id",
                "player_id",
                "is_home",
                "action",
                "minutes",
                "overload_minutes",
            ]
        )
        cprint(f"OK", color=TextColor.GREEN.value)