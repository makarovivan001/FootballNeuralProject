from asgiref.sync import sync_to_async
from django.conf import settings

from application.services.common.custom_print import cprint
from domain.enums.print_colors import TextColor
from parser.management.commands.repositories.player.position import ParserPlayerPositionRepository
from parser.management.commands.repositories.player.role import ParserPlayerRoleRepository
from parser.management.commands.repositories.player.statistic import ParserPlayerStatisticRepository
from parser.management.commands.schemas.player.main import ParserPlayerCreateDTO, ParserPlayerUpdateDTO
from parser.management.commands.services.load_data_service import LoadDataService
from player.models import Player


class ParserPlayerRepository:
    def __init__(
            self,
            player_position_repository: ParserPlayerPositionRepository,
            player_role_repository: ParserPlayerRoleRepository,
            player_statistic_repository: ParserPlayerStatisticRepository,
            load_player: LoadDataService,
            dir_url,
            light_blue_color,
    ):
        self.player_position_repository = player_position_repository
        self.player_role_repository = player_role_repository
        self.player_statistic_repository = player_statistic_repository

        self.load_player = load_player
        self.dir_url = settings.BASE_DIR / dir_url
        self.light_blue_color = light_blue_color

    async def get_from_clubs(self, clubs: list[dict], club_db_ids: dict) -> list[dict]:
        cprint("Начало созданя/обновления игрков из клубов...", color=TextColor.YELLOW.value)
        all_players = []
        all_player_ids = []

        for club in clubs:
            cprint(f"Сбор игроков для ({club['details']['id']}) {club['details']['name']}...", color=TextColor.YELLOW.value, end=" ")
            squad = club['squad']['squad']
            if not squad:
                cprint("")
                continue
            for role in club['squad']['squad']:
                player_ids = []
                role_title = role['title']
                for player in role['members']:
                    if player['id'] in all_player_ids:
                        continue
                    all_player_ids.append(player['id'])
                    player_ids.append(player['id'])
                else:
                    cprint("OK", color=TextColor.GREEN.value)
                    players = await self.get(player_ids)

                    for player in players:
                        player['club_id'] = club_db_ids[club['details']['id']]
                        player['role_ids'] = [await self.player_role_repository.get_or_create(role_title)]

                        player['statistic_id'] = await self.player_statistic_repository.create_or_update(player)

                    all_players += players

        return all_players

    async def get(self, player_ids: list[int] | set[int]) -> list[dict]:
        if isinstance(player_ids, set):
            player_ids = list(player_ids)

        players = await sync_to_async(self.load_player.get_data)(player_ids)

        return players

    async def create_or_update(self, players: list[dict], add_statistic=False) -> dict:
        cprint("Начало созданя/обновления игроков...", color=TextColor.YELLOW.value)
        for_update = []
        for_create = []

        for player_data in players:
            position_id = None
            try:
                if position := player_data['positionDescription']['primaryPosition']['label']:
                    position_id = await self.player_position_repository.get_or_create(position)
            except Exception as exc:
                ...

            player_data['position_id'] = position_id

            if add_statistic:
                # TODO: У Кисляка нет статистики у меня, а у Вани есть
                player_data['statistic_id'] = await self.player_statistic_repository.create_or_update(player_data)

            player_create_dto = ParserPlayerCreateDTO(**player_data)

            cprint(f"{player_create_dto.identifier}) {player_create_dto.surname} {player_create_dto.name}", color=self.light_blue_color, end=" -> ")

            try:
                player = await Player.objects.aget(identifier=player_create_dto.identifier)
                player_update_dto = ParserPlayerUpdateDTO(**player_data)
                player_update_dto.id = player.id
                for_update.append(
                    Player(**player_update_dto.model_dump())
                )
                cprint(f"Добавлено на обновление", color=TextColor.GREEN.value)
            except Player.DoesNotExist:
                for_create.append(
                    Player(**player_create_dto.model_dump())
                )
                cprint(f"Добавлено на создание", color=TextColor.GREEN.value)
            except TypeError as exc:
                ...

        if len(for_update) != 0:
            await self.__update_players(for_update)

        if len(for_create) != 0:
            await self.__create_players(for_create)

        return await self.get_db_ids()

    async def __create_players(self, players: list[Player]) -> None:
        cprint(f"Создание игроков...", color=TextColor.YELLOW.value, end=" ")
        await Player.objects.abulk_create(
            players,
            batch_size=1000
        )
        cprint(f"OK", color=TextColor.GREEN.value)

    async def __update_players(self, players: list[Player]) -> None:
        cprint(f"Обновление игроков...", color=TextColor.YELLOW.value, end=" ")
        await Player.objects.abulk_update(
            players,
            batch_size=1000,
            fields=[
                "club_id", "surname", "name", "height",
                "age", "number", "country", "role_ids", "position_id", "preferred_foot",
                "statistic_id"
            ]
        )
        cprint(f"OK", color=TextColor.GREEN.value)

    async def get_db_ids(self) -> dict:
        cprint(f"Получение словаря с identifier: id ...", color=self.light_blue_color, end=" ")
        player_db_ids = {
            player.identifier: player.id
            async for player in Player.objects.all().order_by('identifier')
        }

        cprint(f"OK", color=TextColor.GREEN.value)
        return player_db_ids