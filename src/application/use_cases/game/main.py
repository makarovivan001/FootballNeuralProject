import  copy
from adrf.requests import AsyncRequest
from django.db.models import Q

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
            player_game_statistic_repository: IPlayerGameStatisticRepository
    ):
        self.game_repository = game_repository
        self.statistic_repository = statistic_repository
        self.history_repository = history_repository
        self.player_repository = player_repository
        self.player_game_statistic_repository = player_game_statistic_repository

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

            param = ~Q(role_ids__contains=[1])

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

    @staticmethod
    def __get_player_data(player_ids: list, player_dtos: dict) -> list:
        players = []
        for player_id in player_ids:
            players.append(player_dtos[player_id].model_dump())

        return players
