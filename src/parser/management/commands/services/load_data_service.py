import json
import os

import requests
from django.conf import settings

from application.services.common.custom_print import cprint
from domain.enums.print_colors import TextColor, BackgroundColor
from parser.management.commands.enums.object_name import ObjectName


class LoadDataService:
    """
    Нужен для получение данных с сайта
    Если в контейнере поставить updating = True, то данные срарсятся по-новой

    """
    def __init__(
            self,
            obj_name,
            dir_url,
            url,
            user_agent,
            x_mas,
            updating
    ):
        self.obj_name = obj_name
        self.dir_url = settings.BASE_DIR / dir_url
        self.url = url
        self.headers = {
            "User-Agent": user_agent,
            "x-mas": x_mas,
        }
        self.updating = updating

    def get_data(self, ids: list[int | str]) -> list[dict]:
        data = []
        cprint(f"Получение данных для", color=TextColor.YELLOW.value, end=' ')
        cprint(f"  ${self.obj_name}  ", color=TextColor.RED.value, backgroud=BackgroundColor.LIGHT_WHITE.value)
        for number, obj_id in enumerate(ids):
            number += 1
            obj_id = f"{obj_id}"
            file_name = f"{obj_id.replace('/', '_')}"
            json_path = self.dir_url / f"{file_name}.json"
            if json_path.exists() and not self.updating:
                cprint(f"{number}. Файл {file_name}.json существует", color=TextColor.GREEN.value, end=' -> ')
                cprint(f"Получение данных из {file_name}.json", color=TextColor.YELLOW.value, end=' -> ')
                with open(json_path, "r") as file:
                    info = json.load(file)
                    data.append(info)
                    cprint("OK", color=TextColor.GREEN.value)
            else:
                cprint(f"{number}. Скачивание данных...", color=TextColor.YELLOW.value, end=' -> ')
                url = self.url.format(obj_id=obj_id)
                response = requests.get(url, headers=self.headers)

                if response.status_code == 200:
                    cprint("OK", color=TextColor.GREEN.value, end=' -> ')
                    responce_data = response.json()

                    if responce_data is None:
                        cprint("NO", color=TextColor.RED.value)
                        continue

                    if self.obj_name == ObjectName.seasons.value:
                        responce_data = responce_data["matches"]["allMatches"]

                    data.append(responce_data)

                    self.__save_json_to_file(responce_data, file_name)
                else:
                    cprint("Не скачалось!", color=TextColor.RED.value)
        return data

    def __save_json_to_file(self, responce_data: dict, file_name: int | str):
        cprint(f"Сохранение в {file_name}.json", color=TextColor.YELLOW.value, end=' -> ')

        file_path = self.dir_url / f"{file_name}.json"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(responce_data, file, ensure_ascii=False, indent=4)

            cprint("OK", color=TextColor.GREEN.value)