import asyncio

from asgiref.sync import sync_to_async
from django.conf import settings

from application.services.common.custom_print import cprint
from domain.enums.print_colors import TextColor
from parser.management.commands.services.load_data_service import LoadDataService
from parser.management.commands.enums.seasons import seasons as all_seasons
from season.models import Season


class ParserSeasonRepository:
    def __init__(
            self,
            load_season: LoadDataService,
            dir_url,
    ):
        self.load_season = load_season
        self.dir_url = settings.BASE_DIR / dir_url

    async def get(self) -> list[dict]:
        seasons = await sync_to_async(self.load_season.get_data)(all_seasons)

        return seasons

    async def get_club_ids(self, seasons: list[dict]) -> set[int]:
        club_ids = set()
        for season in seasons:
            for match in season:
                club_ids.add(match['home']['id'])
                club_ids.add(match['away']['id'])

        return club_ids

    async def get_game_ids(self, seasons: list[dict]) -> dict:
        game_ids = {}
        for i, season in enumerate(seasons):
            if not game_ids.get(all_seasons[i], False):
                game_ids[all_seasons[i]] = []
            for match in season:
                game_ids[all_seasons[i]].append(match['id'])

        return game_ids

    async def get_or_create(self, season_name: str) -> int:
        cprint("Получение id сезона...", color=TextColor.YELLOW.value, end=' ')
        season_name = season_name.replace('_', '/')
        season, created = await Season.objects.aget_or_create(
            name=season_name,
        )

        if created:
            cprint("СОЗДАН!", color=TextColor.GREEN.value)
        else:
            cprint("НАЙДЕН!", color=TextColor.GREEN.value)

        return season.id
