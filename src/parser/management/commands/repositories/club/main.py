from asgiref.sync import sync_to_async
from django.conf import settings

from application.services.common.custom_print import cprint
from club.models import Club
from domain.enums.print_colors import TextColor
from parser.management.commands.schemas.club.main import ParserClubCreateDTO, ParserClubUpdateDTO
from parser.management.commands.services.load_data_service import LoadDataService


class ParserClubRepository:
    def __init__(
            self,
            load_clubs: LoadDataService,
            dir_url,
            light_magenta_color,
    ):
        self.load_clubs = load_clubs
        self.dir_url = settings.BASE_DIR / dir_url
        self.light_magenta_color = light_magenta_color

    async def get(self, club_ids: list[int] | set[int]) -> list[dict]:
        if isinstance(club_ids, set):
            club_ids = list(club_ids)

        clubs = await sync_to_async(self.load_clubs.get_data)(club_ids)

        for club in clubs:
            if club is None:
                clubs.remove(club)

        return clubs


    async def create_or_update(self, clubs: list[dict]) -> dict:
        cprint("Начало созданя/обновления компаний...", color=TextColor.YELLOW.value)
        for_update = []
        for_create = []

        for club_data in clubs:
            club_create_dto = ParserClubCreateDTO(**club_data)
            cprint(f"{club_create_dto.identifier}) {club_create_dto.name}", color=self.light_magenta_color, end=" -> ")

            try:
                club = await Club.objects.aget(identifier=club_create_dto.identifier)
                club_update_dto = ParserClubUpdateDTO(id=club.id, **club_data)
                for_update.append(
                    Club(**club_update_dto.model_dump())
                )
                cprint(f"Добавлено на обновление", color=TextColor.GREEN.value)
            except Club.DoesNotExist:
                for_create.append(
                    Club(**club_create_dto.model_dump())
                )
                cprint(f"Добавлено на создание", color=TextColor.GREEN.value)

        if len(for_update) != 0:
            await self.__update_clubs(for_create)

        if len(for_create) != 0:
            await self.__create_clubs(for_create)

        return await self.get_db_ids()


    async def __create_clubs(self, clubs: list[Club]) -> None:
        cprint(f"Создание клубов...", color=TextColor.YELLOW.value, end=" ")
        await Club.objects.abulk_create(
            clubs,
            batch_size=1000
        )
        cprint(f"OK", color=TextColor.GREEN.value)

    async def __update_clubs(self, clubs: list[Club]) -> None:
        cprint(f"Обновление клубов...", color=TextColor.YELLOW.value, end=" ")
        await Club.objects.abulk_update(
            clubs,
            batch_size=1000,
            fields=[
                "name",
                "stadium_name",
                "stadium_count_of_sits",
                "city_name",
            ]
        )
        cprint(f"OK", color=TextColor.GREEN.value)

    async def get_db_ids(self) -> dict:
        cprint(f"Получение словаря с identifier: id ...", color=self.light_magenta_color, end=" ")
        club_db_ids = {
            club.identifier: club.id
            async for club in Club.objects.all()
        }

        cprint(f"OK", color=TextColor.GREEN.value)
        return club_db_ids