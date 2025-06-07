from application.services.common.custom_print import cprint
from domain.enums.print_colors import TextColor
from parser.management.commands.schemas.player.statistic import ParserPlayerStatisticCreateDTO, \
    ParserPlayerStatisticUpdateDTO
from player.models import Position, PlayerStatistic


class ParserPlayerStatisticRepository:
    def __init__(
            self,
            light_blue_color,
    ):
        self.light_blue_color = light_blue_color
        self.main_stats = [
            "goals",
            "ShotsOnTarget",
            "yellow_cards",
            "red_cards",
            "assists",
            "chances_created",
            "dribbles_succeeded",
            "dispossessed",
        ]

    async def create_or_update(self, player: dict) -> int | None:
        statistic_data = {}
        cprint(f"Попытка добавления статистики для {player['id']}) {player['name']}", color=self.light_blue_color, end=" -> ")

        if main_league_stats := player.get('mainLeague', False):
            if personal_stats := main_league_stats.get('stats', False):
                for league_stats in personal_stats:
                    if league_stats['title'] == "Started":
                        statistic_data["started"] = league_stats['value']
                    elif league_stats['title'] == "Matches":
                        statistic_data["matches_uppercase"] = league_stats['value']
                    elif league_stats['title'] == "Minutes played":
                        statistic_data["minutes_played"] = league_stats['value']
                    elif league_stats['title'] == "Rating":
                        statistic_data["rating"] = league_stats['value']

        statistic: dict | bool = player.get('firstSeasonStats', False)
        if statistic:
            cprint(f"Есть статистика", color=TextColor.GREEN.value, end=" -> ")
            statistic: dict | bool = statistic.get('statsSection', False)
            if statistic:
                for stat_items in statistic['items']:
                    for stat in stat_items['items']:
                        statistic_data[stat['localizedTitleId']] = round(stat['per90'], 2)

                        if stat['localizedTitleId'] in self.main_stats:
                            statistic_data["all_" + stat['localizedTitleId']] = self.__convert_to_number(stat['statValue'])

            player_statistic_create_dto = ParserPlayerStatisticCreateDTO(**statistic_data)
            cprint(f"Добавление...", color=TextColor.YELLOW.value, end=" -> ")

            try:
                player_statistic = await PlayerStatistic.objects.aget(player__identifier=player['id'])
                player_statistic_update_dto = ParserPlayerStatisticUpdateDTO(id=player_statistic.id, **statistic_data)

                await self.__update_players(player_statistic_update_dto)
                return player_statistic_update_dto.id
            except PlayerStatistic.DoesNotExist as exc:
                player_statistic_id = await self.__create_players(player_statistic_create_dto)
                return player_statistic_id

        else:
            cprint(f"Нет статистики", color=TextColor.RED.value)


    async def __create_players(self, player_statistic_create_dto: ParserPlayerStatisticCreateDTO) -> int:
        cprint(f"Создание статистики...", color=TextColor.YELLOW.value, end=" ")
        player_statistic = await PlayerStatistic.objects.acreate(
            **player_statistic_create_dto.model_dump(),
        )
        cprint(f"OK", color=TextColor.GREEN.value)
        return player_statistic.id


    async def __update_players(self, player_statistic_update_dto: ParserPlayerStatisticUpdateDTO) -> None:
        cprint(f"Обновление статистики...", color=TextColor.YELLOW.value, end=" ")
        await PlayerStatistic.objects.filter(
            id=player_statistic_update_dto.id
        ).aupdate(**player_statistic_update_dto.model_dump())
        cprint(f"OK", color=TextColor.GREEN.value)

    def __convert_to_number(self, value: str) -> int | float:
        try:
            value = int(value)
        except ValueError:
            value = float(value)

        return value