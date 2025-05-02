from dependency_injector.wiring import inject, Provide
from django.core.management import BaseCommand
import requests
from bs4 import BeautifulSoup
from .parsers.container import Container
from .parsers.get_clubs import ParserUseCase


class Command(BaseCommand):
    """
    Порядок деействия парсера

    1. Получить все матчи за все сезоны      ✅
    2. По матчу получить:
        1. Инфу о клубах
            (слделать запрос к "https://www.fotmob.com/api/teams?id={club_id}&ccode3=RUS")
            {
                identifier              ["details"]["id"]
                name                    ["details"]["shortName"]
                photo_url?              ["details"]["sportsTeamJSONLD"]["logo"]
                stadium_name?           ["overview"]["venue"]["widget"]["name"]
                stadium_count_of_sits?  ["overview"]["venue"]["statPairs"][1][1]
                city_name               ["overview"]["venue"]["widget"]["city"]
                placement               ["overview"]["lastLineupStats"]["formation"] и ["starters"]
                players (для next шага) ["squad"]: list из dict["members"]: list из dict["id"]
            }
        2. Инфу об игроке
            (слделать запрос к "https://www.fotmob.com/api/playerData?id={player_id}")
            {
                identifier      ["id"]
                club            <передаём с прошлого шага>
                photo?
                surname         ["name"].split()[1]
                name            ["name"].split()[0]
                height          ["playerInformation"][0]["value"]["numberValue"]
                country         ["playerInformation"][4]["value"]["fallback"]
                age             ["playerInformation"][2]["value"]["numberValue"]
                position        []
            }
        3. Статистику по игроку за матч


    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        container = Container()
        container.wire(modules=[__name__])

    # def add_arguments(self, parser):
    #     parser.add_argument('-help', action='store_true')
    #     parser.add_argument('-print', nargs='+', type=str)

    @inject
    def handle(
            self,
            parser_use_case: ParserUseCase = Provide[Container.parser_use_case],
            *args,
            **options
    ):
        parser_use_case.get_info()
        # self.stdout.write(self.style.SUCCESS("Parser started..."))
        # self.stdout.write(self.style.ERROR("Parser Error..."))

