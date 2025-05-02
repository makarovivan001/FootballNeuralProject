import json
import os

import requests
from bs4 import BeautifulSoup
from django.conf import settings

from common.management.commands.parsers.repositories.interfaces.club import IClubRepositoryParser
from common.management.commands.parsers.repositories.interfaces.game import IGameRepositoryParser

seasons = [
    "2010",
    "2011/2012",
    "2012/2013",
    "2013/2014",
    "2014/2015",
    "2015/2016",
    "2016/2017",
    "2017/2018",
    "2018/2019",
    "2019/2020",
    "2020/2021",
    "2021/2022",
    "2022/2023",
    "2023/2024",
    "2024/2025",
]


class ParserUseCase:
    """
    По ссылке "https://www.fotmob.com/api/teams?id=8710&ccode3=RUS" по ключу "squad"
    Находится состав команды (тренер, вратари, защитники, полузащитники, нападающие). По ключу «members», по ключу «id» находится айди игрока

    По ссылке «https://www.fotmob.com/api/playerData?id=1026513"

    """
    def __init__(
            self,
            club_repository_parser: IClubRepositoryParser,
            game_repository_parser: IGameRepositoryParser,
            url,
            dir_url,
            user_agent,
            x_mas
    ):
        self.club_repository_parser = club_repository_parser
        self.game_repository_parser = game_repository_parser
        self.url = url
        self.dir_url = settings.BASE_DIR / dir_url
        self.headers = {
            "User-Agent": user_agent,
            "x-mas": x_mas,
        }

    def save_json_to_file(self, data: dict, file_path: str):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

    def get_info(self) -> None:
        # TODO: Перед запуском раскомментировать
        self.get_matches_to_file()
        club_ids = self.get_matches_info()
        self.club_repository_parser.get_clubs(club_ids)
        self.game_repository_parser.get_seasons()

    def get_matches_to_file(self):
        for season in seasons:
            url = self.url.format(season=season)
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                print(f"{season}")
                self.save_json_to_file(response.json()["matches"]["allMatches"], f"{self.dir_url}/seasons/{season.replace('/', '_')}.json")

            else:
                print(response.status_code)
                print(response.text)
                print("Error")

    def get_matches_info(self) -> set[int]:
        club_ids = set()
        for filename in os.listdir(self.dir_url / "seasons"):
            if filename.endswith(".json"):
                with open(self.dir_url / "seasons" / filename, "r") as file:
                    matches = json.load(file)
                    for match in matches:
                        club_ids.add(match['home']['id'])
                        club_ids.add(match['away']['id'])

        return club_ids