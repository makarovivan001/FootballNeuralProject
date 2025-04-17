import json
import os

import requests
from bs4 import BeautifulSoup


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



class ClubsParser:
    def __init__(
            self,
            url,
            dir_url,
            user_agent,
            x_mas
    ):
        self.url = url
        self.dir_url = dir_url
        self.headers = {
            "User-Agent": user_agent,
            "x-mas": x_mas,
        }

    def save_json_to_file(self, data: dict, file_path: str):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

    def get_info(self) -> None:
        self.get_matches_to_file()

    def get_matches_to_file(self):
        for season in seasons:
            url = self.url.format(season=season)
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                print(f"{season}")
                self.save_json_to_file(response.json()["matches"]["allMatches"], f"{self.dir_url}seasons/{season.replace('/', '_')}.json")
            else:
                print("Error")

    def get_matches_info(self):
        for filename in os.listdir(self.dir_url + "seasons"):
            if filename.endswith(".json"):
                with open(self.dir_url + "seasons/" + filename, "r") as file:
                    matches = json.load(file)

