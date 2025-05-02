import json
import os

from django.conf import settings
import requests

from application.services.common.custom_print import cprint
from club.models import Club
from common.management.commands.parsers.repositories.interfaces.player import IPlayerRepositoryParser
from common.management.commands.parsers.schemas.player import ParserPlayerCreateDTO, PlayerPositionIdRetrieveDTO, \
    ParserStatisticIdDTO, ParserPlayerIdentifierRetrieveDTO, ParserPlayerStatisticCreateDTO
from domain.enums.print_colors import TextColor
from player.models import Player, Position, Statistic


class PlayerRepositoryParser(IPlayerRepositoryParser):
    def __init__(
            self,
            url,
            dir_url,
            user_agent,
            x_mas,
    ):
        self.url = url
        self.dir_url = settings.BASE_DIR / dir_url
        self.headers = {
            "User-Agent": user_agent,
            "x-mas": x_mas,
        }

    def create_for_club(self, squad: list[dict], club_id_dto) -> None:
        if squad:
            for players in squad:
                position_id_dto = self.__position_get_or_create(players['title'])
                for player in players["members"]:

                    player_create_dto = ParserPlayerCreateDTO(
                        club_id=club_id_dto.id,
                        position_id=position_id_dto.id,
                        **player
                    )
                    player_id_dto = self.__get_or_create(player_create_dto)
                    player_statistic_id_dto = self.get_player_statistic(player_id_dto)
                    # if player_statistic_id_dto:
                    #     ...

    def __get_or_create(self, user_create_dto: ParserPlayerCreateDTO) -> ParserPlayerIdentifierRetrieveDTO:
        user_create = user_create_dto.model_dump()
        position_id = user_create.pop("position_id")

        player, created = Player.objects.get_or_create(
            identifier=user_create_dto.identifier,
            defaults=user_create,
        )

        player.position.add(position_id)

        return ParserPlayerIdentifierRetrieveDTO.model_validate(player)


    def __position_get_or_create(self, position_title: str) -> PlayerPositionIdRetrieveDTO:
        position, created = Position.objects.get_or_create(
            name=position_title,
        )

        return PlayerPositionIdRetrieveDTO.model_validate(position)


    def save_json_to_file(self, data: dict, file_path: str):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

    def get_player_statistic(self, player_dto: ParserPlayerIdentifierRetrieveDTO) -> ParserStatisticIdDTO | None:
        start_player_statistic_parser = True
        json_path = self.dir_url / f"{player_dto.identifier}.json"
        if json_path.exists():
            start_player_statistic_parser = False

        statistic_data = {}

        if start_player_statistic_parser:
            url = self.url.format(player_id=player_dto.identifier)
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                player = response.json()

                print(f"{player_dto.identifier}")
                self.save_json_to_file(player, f"{self.dir_url}/{player_dto.identifier}.json")
        else:
            with open(json_path, "r") as file:
                player = json.load(file)

        stats = player.get('firstSeasonStats', False)
        if stats:
            stats = stats.get('statsSection', False)

        if stats:
            for stat_items in stats['items']:
                for stat in stat_items['items']:
                    statistic_data[stat['localizedTitleId']] = round(stat['per90'], 2)

            parser_statistic_create_dto = ParserPlayerStatisticCreateDTO(**statistic_data)

            if not player_dto.statistic_id:
                statistic = Statistic.objects.create(
                    **parser_statistic_create_dto.model_dump()
                )

                player = Player.objects.get(identifier=player_dto.identifier)
                player.statistic = statistic
                player.save()
                print(f"Добавлена статистика")
            else:
                statistic = Statistic.objects.filter(
                    id=player_dto.statistic_id,
                ).update(**parser_statistic_create_dto.model_dump())

                # club_create_dto = ParserClubCreateDTO(**club)
                # club_id_dto = self.get_or_create(club_create_dto)
                #
                # self.player_repository_parser.create_for_club(club['squad']['squad'], club_id_dto)


    def __create_one_player(self, player_identifier_id: int, club_identifier: int) -> ParserPlayerIdentifierRetrieveDTO:
        cprint(f"Получение нового игрока {player_identifier_id} для клуба {club_identifier}", end=' -> ')
        url = self.url.format(player_id=player_identifier_id)
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            player: dict = response.json()

            self.save_json_to_file(player, f"{self.dir_url}/{player_identifier_id}.json")

            # Знаю, не надо так, но как иначе?
            # Закомментил добавление клуба в игрока который уже не находится в этом клубе
            # club = Club.objects.get(identifier=club_identifier)

            height = ''
            age = ''
            cname = ''
            for player_info in player["playerInformation"]:
                if player_info['title'] == 'Age':
                    age = player_info["value"]["numberValue"]
                elif player_info['title'] == 'Height':
                    height = player_info["value"]["numberValue"]
                elif player_info['title'] == 'Country' or player_info['title'] == 'Country/Region':
                    cname = player_info["value"]["fallback"]
            player.update({
                "identifier": player_identifier_id,
                # Закомментил добавление клуба в игрока который уже не находится в этом клубе
                # "club_id": club.id,
                "height": height,
                "age": age,
                "cname": cname,
            })
            player_create_dto = ParserPlayerCreateDTO(**player)
            player_obj = Player.objects.create(
                **player_create_dto.model_dump(exclude_none=True)
            )
            cprint(f"Добавлен!", color=TextColor.GREEN.value)
            return ParserPlayerIdentifierRetrieveDTO.model_validate(player_obj)

    def get_by_identifier(self, identifiers: list[dict]) -> dict:
        player_ids = {}
        for identifier in identifiers:
            try:
                player = Player.objects.get(identifier=identifier['id'])
                player_ids[player.identifier] = player.id
            except Player.DoesNotExist:
                player_id_dto = self.__create_one_player(
                    identifier['id'],
                    identifier['club_id'],
                )
                self.get_player_statistic(player_id_dto)
                player_ids[player_id_dto.identifier] = player_id_dto.id

        return player_ids