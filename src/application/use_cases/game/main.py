import  copy
import json

from adrf.requests import AsyncRequest
from asgiref.sync import sync_to_async
from django.db.models import Q

from application.services.game.prediction_position import LineupProbabilityCalculator
from domain.exceptions.repositories.main import RepositoryConnectionDoesNotExistError
from domain.exceptions.use_cases.common import RepositoryDoesNotExist
from domain.interfaces.repositories.game.history import IHistoryRepository
from domain.interfaces.repositories.game.main import IGameRepository
from domain.interfaces.repositories.game.statistic import IStatisticRepository
from domain.interfaces.repositories.player.game_statistic import IPlayerGameStatisticRepository
from domain.interfaces.repositories.player.main import IPlayerRepository
from domain.interfaces.use_cases.game.main import IGameUseCase
from domain.schemas.player.main import PlayerShortRetrieveDTO


class GameUseCase(IGameUseCase):
    def __init__(
            self,
            game_repository: IGameRepository,
            statistic_repository: IStatisticRepository,
            history_repository: IHistoryRepository,
            player_repository: IPlayerRepository,
            player_game_statistic_repository: IPlayerGameStatisticRepository,
            lineup_probability_calculator: LineupProbabilityCalculator
    ):
        self.game_repository = game_repository
        self.statistic_repository = statistic_repository
        self.history_repository = history_repository
        self.player_repository = player_repository
        self.player_game_statistic_repository = player_game_statistic_repository
        self.lineup_probability_calculator = lineup_probability_calculator

    async def get_page_info(
            self, request: AsyncRequest, game_id: int
    ) -> dict:
        try:
            game_dto = await self.game_repository.get_by_id(game_id)

        except RepositoryConnectionDoesNotExistError:
            raise RepositoryDoesNotExist

        player_ids = game_dto.home_players + game_dto.away_players
        players_data = await self.player_repository.get_by_ids(
            player_ids,
            dto_model=PlayerShortRetrieveDTO,
        )

        statistics = {}
        histories = []
        player_game_statistic = {}

        if game_dto.is_finished:
            histories_dto = await self.history_repository.get_for_game(
                game_id=game_id,
            )

            histories = [
                history.model_dump()
                for history in histories_dto
            ]

            for history in histories:
                history_copy = copy.deepcopy(history)
                history_copy.pop('player')

                if history['swap'] is not None:
                    history_copy.pop('swap')
                    swap = history['swap'].copy()
                    history['swap'] = self.__get_player_data(history['swap'], players_data)

                    for player_id in swap:
                        players_data[player_id].actions.append(history_copy)
                else:
                    players_data[history['player']['id']].actions.append(history_copy)

            for placement in game_dto.home_club_placement + game_dto.away_club_placement:
                for player in placement:
                    player["player"] = players_data[player['id']].model_dump()

            game_dto.home_players = self.__get_player_data(game_dto.home_players, players_data)
            game_dto.away_players = self.__get_player_data(game_dto.away_players, players_data)

            statistics_dto = await self.statistic_repository.get_for_game(
                game_id=game_id,
                home_club_id=game_dto.home_club.id,
                away_club_id=game_dto.away_club.id,
            )

            player_game_statistic_dtos = await self.player_game_statistic_repository.get_for_game_page(
                game_id=game_id
            )

            player_game_statistic = {
                game_statistic.player.id: game_statistic.model_dump()
                for game_statistic in player_game_statistic_dtos

            }

            statistics = statistics_dto.model_dump()
        else:
            game_dto.home_club_placement = await self.game_repository.get_last_placement(club_id=game_dto.home_club.id)
            game_dto.away_club_placement = await self.game_repository.get_last_placement(club_id=game_dto.away_club.id)

            param = ~Q(primary_position_id=1)

            home_club_players = [
                player_dto.model_dump()
                for player_dto in await self.player_repository.get_by_club_id(
                    club_id=game_dto.home_club.id,
                    dto_model=PlayerShortRetrieveDTO,
                    param=param,
                )

            ]
            away_club_players = [
                player_dto.model_dump()
                for player_dto in await self.player_repository.get_by_club_id(
                    club_id=game_dto.away_club.id,
                    dto_model=PlayerShortRetrieveDTO,
                    param=param,
                )
            ]
            game_dto.home_players = home_club_players
            game_dto.away_players = away_club_players

            game_dto.away_score = "?"
            game_dto.home_score = "?"

        game = game_dto.model_dump()

        return {
            'game': game,
            'statistics': statistics,
            'histories': histories,
            'player_game_statistic': player_game_statistic,
        }

    async def get_lineup_probability(self, request: AsyncRequest, game_id: int) -> dict:
        data = request.query_params

        if 'club_id' not in data:
            return {"error": "Отсутствует club_id", "probability": 0.0, "info": []}

        if 'placement' not in data:
            return {"error": "Отсутствует placement", "probability": 0.0, "info": []}

        club_id = data['club_id']
        placement_raw = data['placement']

        try:
            club_id = int(club_id)
        except ValueError as e:
            return {"error": f"Неверный club_id: {club_id}", "probability": 0.0, "info": []}

        try:
            placement = json.loads(placement_raw)
        except json.JSONDecodeError as e:
            return {"error": f"Неверный JSON: {str(e)}", "probability": 0.0, "info": []}

        if not isinstance(placement, list):
            return {"error": "placement должен быть списком", "probability": 0.0, "info": []}

        if len(placement) == 0:
            return {"error": "placement пустой", "probability": 0.0, "info": []}

        for line_idx, line in enumerate(placement):
            if not isinstance(line, list):
                return {"error": f"Линия {line_idx} должна быть списком", "probability": 0.0, "info": []}

            if len(line) == 0:
                continue

            for player_idx, player_data in enumerate(line):
                if not isinstance(player_data, dict):
                    return {"error": f"Неверный формат данных игрока в линии {line_idx}", "probability": 0.0,
                            "info": []}

                required_fields = ['id', 'position_id']
                for field in required_fields:
                    if field not in player_data:
                        if field == 'id' and 'player_id' in player_data:
                            player_data['id'] = player_data['player_id']
                        else:
                            return {"error": f"Отсутствует поле '{field}' у игрока", "probability": 0.0, "info": []}

                try:
                    player_id = int(player_data['id'])
                    position_id = int(player_data['position_id'])

                    player_data['id'] = player_id
                    player_data['position_id'] = position_id

                except (ValueError, TypeError) as e:
                    return {"error": f"Неверный тип данных у игрока: {str(e)}", "probability": 0.0, "info": []}

        result = await sync_to_async(self.lineup_probability_calculator.get_probability)(
            game_id=game_id,
            club_id=club_id,
            proposed_squad=placement,
        )

        return result

    @staticmethod
    def __get_player_data(player_ids: list, player_dtos: dict) -> list:
        players = []
        for player_id in player_ids:
            players.append(player_dtos[player_id].model_dump())

        return players

