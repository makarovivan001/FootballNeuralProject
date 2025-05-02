import json
import os

import requests
from django.conf import settings

from application.services.common.custom_print import cprint
from common.management.commands.parsers.repositories.interfaces.club import IClubRepositoryParser
from common.management.commands.parsers.repositories.interfaces.game import IGameRepositoryParser
from common.management.commands.parsers.repositories.interfaces.player import IPlayerRepositoryParser
from common.management.commands.parsers.schemas.game import ParserGameIdRetrieveDTO, ParserGameCreateDTO
from domain.enums.print_colors import TextColor
from game.models import Game


class GameRepositoryParser(IGameRepositoryParser):
    def __init__(
            self,
            player_repository_parser: IPlayerRepositoryParser,
            club_repository_parser: IClubRepositoryParser,
            url,
            games_dir_url,
            seasons_dir_url,
            user_agent,
            x_mas,
    ):
        self.player_repository_parser = player_repository_parser
        self.club_repository_parser = club_repository_parser

        self.games_dir_url = settings.BASE_DIR / games_dir_url
        self.seasons_dir_url = settings.BASE_DIR / seasons_dir_url

        self.url = url
        self.headers = {
            "User-Agent": user_agent,
            "x-mas": x_mas,
        }

    def __save_json_to_file(self, data: dict, file_path: str):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

    def get_seasons(self) -> None:
        for filename in os.listdir(self.seasons_dir_url):
            if filename.endswith(".json"):
                with open(self.seasons_dir_url / filename, "r") as file:
                    season_data = json.load(file)
                    for match in season_data:
                        self.get_match_info(match['id'])

    def get_match_info(self, match_id: int) -> None:
        cprint(f"{match_id}", end=' - ')

        json_path = self.games_dir_url / f"{match_id}.json"
        if json_path.exists():
            cprint(f"Файл {match_id}.json существует", color=TextColor.YELLOW.value, end=' -> ')
            with open(json_path, "r") as file:
                match = json.load(file)
                match_id_dto = self.get_or_create(match)
        else:
            url = self.url.format(game_id=match_id)
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                match = response.json()

                self.__save_json_to_file(match, f"{self.games_dir_url}/{match_id}.json")
                cprint(f"Сохранено в {match_id}.json", color=TextColor.GREEN.value, end=' -> ')
                match_id_dto = self.get_or_create(match)

        # match_id_dto
        # Тут добавить создание истории

    def get_or_create(self, match: dict) -> ParserGameIdRetrieveDTO:
        cprint(f"Начало сохранения... ", end=' -> ', color=TextColor.YELLOW.value)

        clubs = self.club_repository_parser.get_by_identifier([
            match['general']['homeTeam']['id'],
            match['general']['awayTeam']['id'],
        ])

        home_club_formation: str = match['content']['lineup']['homeTeam']['formation']
        away_club_formation: str = match['content']['lineup']['awayTeam']['formation']

        home_club_player_starters: dict = match['content']['lineup']['homeTeam']
        away_club_player_starters: dict = match['content']['lineup']['awayTeam']

        players_identifiers = []
        for player_obj in home_club_player_starters['starters']:
            players_identifiers.append({
                "id": player_obj['id'],
                "club_id": home_club_player_starters['id'],
            })
        for player_obj in away_club_player_starters['starters']:
            players_identifiers.append({
                "id": player_obj['id'],
                "club_id": away_club_player_starters['id'],
            })

        player_ids_data = self.player_repository_parser.get_by_identifier(players_identifiers)

        # Расстановка домашнего клуба
        home_goalkeeper: dict = home_club_player_starters['starters'].pop(0)
        home_club_placement = [
            [{
                'id': player_ids_data[home_goalkeeper['id']],
                'position_id': home_goalkeeper['positionId']
            }]
        ]
        index = 0
        for count_on_position in list(map(int, home_club_formation.split('-'))):
            home_club_placement.append([])
            for _ in range(count_on_position):
                home_club_placement[-1].append({
                    'id': player_ids_data[home_club_player_starters['starters'][index]['id']],
                    'position_id': home_club_player_starters['starters'][index]['positionId']
                })
                index += 1

        # Расстановка гостевого клуба
        away_goalkeeper: dict = away_club_player_starters['starters'].pop(0)
        away_club_placement = [
            [{
                'id': player_ids_data[away_goalkeeper['id']],
                'position_id': away_goalkeeper['positionId']
            }]
        ]
        index = 0
        for count_on_position in list(map(int, away_club_formation.split('-'))):
            away_club_placement.append([])
            for _ in range(count_on_position):
                away_club_placement[-1].append({
                    'id': player_ids_data[away_club_player_starters['starters'][index]['id']],
                    'position_id': away_club_player_starters['starters'][index]['positionId']
                })
                index += 1

        match.update({
            "home_club_id": clubs[match['general']['homeTeam']['id']],
            "away_club_id": clubs[match['general']['awayTeam']['id']],
            "home_club_placement": home_club_placement,
            "away_club_placement": away_club_placement,
        })
        match_dto = ParserGameCreateDTO(
            **match
        )

        game = Game.objects.get_or_create(
            identifier=match_dto.identifier,
            defaults=match_dto.model_dump(),
        )

        cprint(f"СОХРАНЕНО", color=TextColor.GREEN.value)
        return ParserGameIdRetrieveDTO.model_validate(game)



# История игры
# ['content']['matchFacts']['events']['events']

# Статистика игры
# ['content]['stats]['Periods]['All]['stats']

# def




# other     our
# 7868591 - 2802040 = 5066551
# 7868595 - 2802044 = 5066551