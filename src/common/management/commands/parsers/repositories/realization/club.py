import json
import os
from abc import ABC, abstractmethod

from django.conf import settings
import requests

from club.models import Club
from common.management.commands.parsers.repositories.interfaces.club import IClubRepositoryParser
from common.management.commands.parsers.repositories.interfaces.player import IPlayerRepositoryParser
from common.management.commands.parsers.schemas.club import ParserClubCreateDTO, ParserClubIdRetrieveDTO
from common.management.commands.parsers.schemas.player import PlayerPositionIdRetrieveDTO
from player.models import Position


class ClubRepositoryParser(IClubRepositoryParser):
    def __init__(
            self,
            player_repository_parser: IPlayerRepositoryParser,
            url,
            dir_url,
            user_agent,
            x_mas,
    ):
        self.player_repository_parser = player_repository_parser

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


    def get_clubs(self, club_ids: set[int]) -> None:
        start_club_parser = True
        if self.dir_url.exists() and any(self.dir_url.glob("*.json")):
            start_club_parser = False

        if start_club_parser:
            for club_id in club_ids:
                url = self.url.format(club_id=club_id)
                response = requests.get(url, headers=self.headers)

                if response.status_code == 200:
                    answer = response.json()
                    if not answer:
                        continue
                    print(f"{club_id}) {answer['details']['name']}")
                    self.save_json_to_file(answer, f"{self.dir_url}/{club_id}.json")

                else:
                    print(response.status_code)
                    print(response.text)
                    print("Error")

        self.create_from_ids(club_ids)

    def create_from_ids(self, club_ids: set[int]) -> None:
        for filename in os.listdir(self.dir_url):
            if filename.endswith(".json"):
                with open(self.dir_url / filename, "r") as file:
                    club = json.load(file)
                    print(f"{club['details']['id']}) {club['details']['name']}")
                    club_create_dto = ParserClubCreateDTO(**club)
                    club_id_dto = self.get_or_create(club_create_dto)

                    self.player_repository_parser.create_for_club(club['squad']['squad'], club_id_dto)

    def get_or_create(self, club_create_dto: ParserClubCreateDTO) -> ParserClubIdRetrieveDTO:
        club, created = Club.objects.get_or_create(
            identifier=club_create_dto.identifier,
            defaults=club_create_dto.model_dump(),
        )

        club_id_dto = ParserClubIdRetrieveDTO.model_validate(club)
        return club_id_dto

    def get_by_identifier(self, identifiers: list[int]) -> dict:
        clubs = Club.objects.filter(identifier__in=identifiers)

        return {
            club.identifier: club.id
            for club in clubs
        }