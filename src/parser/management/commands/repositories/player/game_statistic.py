from application.services.common.custom_print import cprint
from domain.enums.print_colors import TextColor
from game.models import GameStatistic
from parser.management.commands.schemas.game.main import ParserGameShortRetrieveDTO
from parser.management.commands.schemas.player.game_statistic import ParserPlayerGameStatisticCreateDTO
from player.models import PlayerGameStatistic


class ParserPlayerGameStatisticRepository:
    def __init__(
            self,
            light_blue_color,
    ) -> None:
        self.light_blue_color = light_blue_color


    async def create_or_update(
        self,
        games_of_seasons: dict,
        game_dtos: dict[int, ParserGameShortRetrieveDTO],
        player_db_ids: dict
    ) -> int | None:
        for_update = []
        for_create = []
        await self.__delete_statistic()

        cprint(f"Попытка добавления статистики для игроков для матчей...", color=TextColor.YELLOW.value)

        for season, games in games_of_seasons.items():
            if season == '2024/2025':
                ...
            for game_data in games:
                game_content: dict[str, dict | None] = game_data.get('content', None)
                if game_content:
                    player_statistics: dict[str, dict] = game_content.get('playerStats', {})
                    if player_statistics is None:
                        continue
                    i = 0
                    try:
                        for i, (item) in enumerate(player_statistics.items()):
                            player_identifier, player_statistic = item

                            player_id = player_db_ids[int(player_identifier)]
                            stats_list = player_statistic.get('stats', [])
                            statistic_data = {}
                            for chapters in stats_list:
                                for stat_name, stat_value in chapters.get('stats', {}).items():
                                    if stat_value['key'] is not None:
                                        type = stat_value['stat']['type']
                                        try:
                                            value = stat_value['stat']['value']
                                        except KeyError:
                                            value = 0
                                        if type == 'fractionWithPercentage':
                                            value = f"{stat_value['stat']['value']}/{stat_value['stat'].get('total', 0)}"

                                        statistic_data[stat_value['key']] = value

                            player_statistic_dto = ParserPlayerGameStatisticCreateDTO(
                                game_id=game_dtos[int(game_data['general']['matchId'])].id,
                                player_id=player_id,
                                **statistic_data,
                            )
                            for_create.append(
                                PlayerGameStatistic(**player_statistic_dto.model_dump())
                            )
                    except Exception as e:
                        print(e)
                        if i > 140:
                            ...
                        ...

        if len(for_update) != 0:
            await self.__update_statistic(for_update)
        if len(for_create) != 0:
            await self.__create_statistic(for_create)
        else:
            cprint(f"Нет статистики", color=TextColor.RED.value)

    async def __delete_statistic(self) -> None:
        cprint(f"Удаление всей статистики игроков...", color=TextColor.YELLOW.value, end=" ")
        await PlayerGameStatistic.objects.all().adelete()
        cprint(f"OK", color=TextColor.GREEN.value)

    async def __create_statistic(self, game_statistic_create_dto: list[PlayerGameStatistic]) -> None:
        cprint(f"Создание статистики...", color=TextColor.YELLOW.value, end=" ")
        await PlayerGameStatistic.objects.abulk_create(
            game_statistic_create_dto,
            batch_size=1000
        )
        cprint(f"OK", color=TextColor.GREEN.value)

    async def __update_statistic(self, game_statistic_update_dto: list[PlayerGameStatistic]) -> None:
        cprint(f"Обновление статистики...", color=TextColor.YELLOW.value, end=" ")
        await PlayerGameStatistic.objects.abulk_update(
            game_statistic_update_dto,
            batch_size=1000,
            fields=[
                "rating_title",
                "minutes_played",
                "goals",
                "assists",
                "total_shots",
                "accurate_passes",
                "chances_created",
                "touches",
                "touches_opp_box",
                "passes_into_final_third",
                "accurate_crosses",
                "long_balls_accurate",
                "corners",
                "dispossessed",
                "tackles_succeeded",
                "clearances",
                "headed_clearance",
                "interceptions",
                "defensive_actions",
                "recoveries",
                "dribbled_past",
                "duel_won",
                "duel_lost",
                "ground_duels_won",
                "aerials_won",
                "was_fouled",
                "fouls",
            ]
        )
        cprint(f"OK", color=TextColor.GREEN.value)