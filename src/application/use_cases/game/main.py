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

    @staticmethod
    def __get_player_data(player_ids: list, player_dtos: dict) -> list:
        players = []
        for player_id in player_ids:
            players.append(player_dtos[player_id].model_dump())

        return players



#     from typing import List, Dict
#
# def calculate_player_probability(player_id: int, proposed_position: int, player_stats: Dict) -> float:
#     """
#     Рассчитывает вероятность выхода игрока на предложенной позиции.
#     player_stats: {
#         'total_matches': int,
#         'matches_played': int,
#         'position_count': {position_id: count},
#         'is_goalkeeper': bool
#     }
#     """
#     total_matches = player_stats['total_matches']
#     matches_played = player_stats['matches_played']
#     pos_count = player_stats['position_count'].get(proposed_position, 0)
#     is_goalkeeper = player_stats['is_goalkeeper']
#
#     if total_matches == 0:
#         return 0
#
#     base_prob = (matches_played / total_matches) * 100
#     if matches_played == 0:
#         # Игрок не играл вообще — вероятность 0
#         return 0
#
#     pos_prob = (pos_count / matches_played) * 100 if matches_played > 0 else 0
#
#     prob = (base_prob + pos_prob) / 2
#
#     # Если вратарь попал в поле (position_id != 11), вероятность = 0
#     if is_goalkeeper and proposed_position != 11:
#         return 0
#
#     # Если полевой игрок попал в ворота (position_id == 11), вероятность = 0
#     if not is_goalkeeper and proposed_position == 11:
#         return 0
#
#     return prob
#
# def calculate_line_probability(line_players: List[Dict], players_stats: Dict[int, Dict]) -> float:
#     """
#     Рассчитывает вероятность линии.
#     line_players — список игроков с position_id и id.
#     players_stats — словарь со статистикой игроков.
#     """
#     probs = []
#     goalkeeper_in_field = False
#     field_player_in_goal = False
#
#     for player in line_players:
#         pid = player['id']
#         pos = player['position_id']
#         stats = players_stats.get(pid)
#         if not stats:
#             # Если нет статистики — вероятность 0
#             prob = 0
#         else:
#             prob = calculate_player_probability(pid, pos, stats)
#
#         # Проверки по позициям:
#         if stats and stats['is_goalkeeper']:
#             if pos != 11:
#                 # Вратарь в поле — вероятность линии падает на 90%
#                 goalkeeper_in_field = True
#         else:
#             if pos == 11:
#                 # Полевой игрок в воротах — вероятность линии 0
#                 field_player_in_goal = True
#
#         probs.append(prob)
#
#     if field_player_in_goal:
#         # Линия с полевым игроком в воротах — вероятность 0
#         return 0.0
#
#     line_prob = sum(probs) / len(probs) if probs else 0
#
#     if goalkeeper_in_field:
#         # Если вратарь в поле — уменьшаем вероятность линии на 90%
#         line_prob *= 0.1
#
#     # Проверяем игроков, которые ни разу не играли на предложенной позиции:
#     # Если хотя бы 1 игрок не играл на позиции — уменьшаем линию на 30%
#     for player in line_players:
#         pid = player['id']
#         pos = player['position_id']
#         stats = players_stats.get(pid)
#         if stats:
#             played_pos_count = stats['position_count'].get(pos, 0)
#             if played_pos_count == 0:
#                 line_prob *= 0.7
#                 break  # Уменьшаем только один раз на линию
#
#     return line_prob
#
# def calculate_formation_probability(proposed_formation: List[List[Dict]], players_stats: Dict[int, Dict], last_formations: List[List[List[Dict]]], formation_history: List[List[List[Dict]]]) -> float:
#     """
#     proposed_formation - текущий состав: список линий, где каждая линия - список игроков с id и position_id
#     players_stats - статистика игроков
#     last_formations - список прошлых 11 составов (аналогичной структуры)
#     formation_history - список прошлых схем (список схем, каждая схема — список линий с position_id)
#     """
#
#     # 1) Считаем вероятность каждой линии
#     line_probs = []
#     for line in proposed_formation:
#         line_prob = calculate_line_probability(line, players_stats)
#         line_probs.append(line_prob)
#
#     # 2) Проверка — если 2 и более линии ниже 35% — вероятность состава 0
#     weak_lines = sum(1 for p in line_probs if p < 35)
#     if weak_lines >= 2:
#         return 0.0
#
#     # 3) Итоговая вероятность как среднее по линиям
#     squad_prob = sum(line_probs) / len(line_probs) if line_probs else 0
#
#     # 4) Рассчёт вероятности схемы (как % повторов этой схемы в последних 11 матчах)
#     # Формат formation_history: список списков линий с position_id
#     # Сравним proposed_formation по схемам с каждым из последних 11
#     def formation_to_signature(formation):
#         # Представим схему как список списков позиций по линиям для сравнения
#         return [[p['position_id'] for p in line] for line in formation]
#
#     proposed_signature = formation_to_signature(proposed_formation)
#     count_same_formation = 0
#     for past_formation in formation_history:
#         past_signature = formation_to_signature(past_formation)
#         if past_signature == proposed_signature:
#             count_same_formation += 1
#
#     formation_prob_percent = (count_same_formation / max(len(formation_history), 1)) * 100
#
#     # 5) Учёт ротации состава:
#     # Считаем среднее количество изменений между соседними составами в last_formations
#     def count_changes(form1, form2):
#         # Количество игроков отличающихся в двух составах
#         ids1 = set()
#         ids2 = set()
#         for line in form1:
#             for p in line:
#                 ids1.add(p['id'])
#         for line in form2:
#             for p in line:
#                 ids2.add(p['id'])
#         return len(ids1.symmetric_difference(ids2))
#
#     changes = []
#     for i in range(len(last_formations) - 1):
#         changes.append(count_changes(last_formations[i], last_formations[i+1]))
#     avg_changes = sum(changes) / len(changes) if changes else 0
#
#     # Считаем изменения между предыдущим составом и текущим (proposed_formation)
#     if last_formations:
#         last_formation = last_formations[-1]
#         current_changes = count_changes(last_formation, proposed_formation)
#     else:
#         current_changes = 0
#
#     # Если текущие изменения сильно превышают средние — уменьшаем вероятность состава
#     # Если же тренер часто ротирует (avg_changes высоко), то уменьшение минимальное
#     # Пример логики (можно настроить):
#     if avg_changes == 0:
#         rotation_factor = 0.5 if current_changes > 0 else 1.0
#     else:
#         ratio = current_changes / avg_changes
#         if ratio <= 1:
#             rotation_factor = 1.0
#         elif ratio <= 1.5:
#             rotation_factor = 0.8
#         else:
#             rotation_factor = 0.6
#
#     # 6) Объединяем вероятность состава с вероятностью схемы (с небольшим весом)
#     # Пусть схема влияет на 20% от итогового результата
#     final_prob = (squad_prob * 0.8) + (formation_prob_percent * 0.2)
#
#     # 7) Умножаем на фактор ротации
#     final_prob *= rotation_factor
#
#     # 8) Проверка на полевого игрока в воротах (prob уже 0 для линии, но по условию итог умножаем на 0.2)
#     # Но это уже учтено в calculate_line_probability и line_probs, просто проверим отдельно
#     goalkeeper_line_prob = calculate_line_probability(proposed_formation[0], players_stats)  # первая линия — вратари
#     if goalkeeper_line_prob == 0:
#         # Если вратарь отсутствует или полевой игрок в воротах (line_prob = 0 для ворот)
#         final_prob *= 0.2
#
#     return max(0, min(final_prob, 100))  # Ограничиваем вероятность от 0 до 100
