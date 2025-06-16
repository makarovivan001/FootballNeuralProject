from enum import Enum

from django.db.models.functions import Concat
from django.db.models import Q, F, Value
from game.models import Game
from player.models import Player
from typing import List, Dict, Tuple, Optional



CURRENT_POSITION_MAP = {
    11: [11],
    31: [32, 31],
    32: [32, 31],
    23: [33, 23, 34, 35, 36, 37, 55],
    33: [33, 23, 34, 35, 36, 37, 55],
    34: [33, 23, 34, 35, 36, 37, 55],
    36: [33, 23, 34, 35, 36, 37, 55],
    37: [33, 23, 34, 35, 36, 37, 55],
    55: [33, 23, 34, 35, 36, 37, 55],
    35: [33, 23, 34, 35, 36, 37, 55],
    38: [38, 39],
    39: [38, 39],
    51: [51, 52, 53, 62],
    52: [51, 52, 53, 62],
    53: [51, 52, 53, 62],
    62: [51, 52, 53, 62],
    57: [57, 58, 59, 68],
    58: [57, 58, 59, 68],
    59: [57, 58, 59, 68],
    68: [57, 58, 59, 68],
    63: [63, 64, 65, 66, 67],
    64: [63, 64, 65, 66, 67],
    65: [63, 64, 65, 66, 67],
    66: [63, 64, 65, 66, 67],
    67: [63, 64, 65, 66, 67],
    71: [71, 72],
    72: [71, 72],
    73: [73, 74, 75, 76, 77],
    74: [73, 74, 75, 76, 77],
    75: [73, 74, 75, 76, 77],
    76: [73, 74, 75, 76, 77],
    77: [73, 74, 75, 76, 77],
    79: [78, 79],
    78: [78, 79],
    82: [82, 83, 102, 103],
    83: [82, 83, 102, 103],
    102: [82, 83, 102, 103],
    103: [82, 83, 102, 103],
    84: [84, 85, 86, 94, 95, 96],
    85: [84, 85, 86, 94, 95, 96],
    86: [84, 85, 86, 94, 95, 96],
    94: [84, 85, 86, 94, 95, 96],
    95: [84, 85, 86, 94, 95, 96],
    96: [84, 85, 86, 94, 95, 96],
    87: [87, 88, 107, 108],
    88: [87, 88, 107, 108],
    107: [87, 88, 107, 108],
    108: [87, 88, 107, 108],
    104: [104, 105, 106, 114, 115, 116],
    105: [104, 105, 106, 114, 115, 116],
    106: [104, 105, 106, 114, 115, 116],
    114: [104, 105, 106, 114, 115, 116],
    115: [104, 105, 106, 114, 115, 116],
    116: [104, 105, 106, 114, 115, 116],
}


class TypeInfo(Enum):
    player = 'player'
    line = 'line'
    other = "other"


class LineupProbabilityCalculator:
    GOALKEEPER_POSITIONS = {11}
    DEFENDER_POSITIONS = {32, 34, 36, 38, 51, 33, 35, 37, 59}
    MIDFIELDER_POSITIONS = {63, 65, 67, 71, 73, 75, 77, 79, 72, 74, 76, 78, 84, 86, 85, 95, 96}
    FORWARD_POSITIONS = {83, 82, 87, 88, 103,  105,  107,  104,  106,  115}

    def __init__(self):
        self.position_categories = {
            'goalkeeper': self.GOALKEEPER_POSITIONS,
            'defender': self.DEFENDER_POSITIONS,
            'midfielder': self.MIDFIELDER_POSITIONS,
            'forward': self.FORWARD_POSITIONS
        }

        self.rivalry_importance_by_club = {
            1: {
                5: 1.4,
                2: 1.4,
                3: 1.4,
                6: 1.4,
                10: 1.4,
                12: 1.4,
                16: 1.4,
                19: 1.4,
                25: 1.4,
                27: 1.4,
                28: 1.4,
                29: 1.4,
                34: 1.4,
                35: 1.4,
                32: 1.4
            },
            2: {
                5: 1.4,
                1: 1.4,
                3: 1.4,
                6: 1.4,
                10: 1.4,
                12: 1.4,
                16: 1.4,
                19: 1.4,
                25: 1.4,
                27: 1.4,
                28: 1.4,
                29: 1.4,
                34: 1.4,
                35: 1.4,
                32: 1.4
            },
            3: {
                5: 1.4,
                2: 1.4,
                1: 1.4,
                6: 1.4,
                10: 1.4,
                12: 1.4,
                16: 1.4,
                19: 1.4,
                25: 1.4,
                27: 1.4,
                28: 1.4,
                29: 1.4,
                34: 1.4,
                35: 1.4,
                32: 1.4
            },
            5: {
                1: 1.9,
                2: 1.6,
                3: 1.4,
                6: 1.4,
                10: 1.4,
                12: 1.4,
                16: 1.4,
                19: 1.4,
                25: 1.4,
                27: 1.4,
                28: 1.4,
                29: 1.4,
                34: 1.4,
                35: 1.4,
                32: 1.4
            },
            6: {
                5: 1.9,
                2: 1.6,
                3: 1.4,
                1: 1.4,
                10: 1.4,
                12: 1.4,
                16: 1.4,
                19: 1.4,
                25: 1.4,
                27: 1.4,
                28: 1.4,
                29: 1.4,
                34: 1.4,
                35: 1.4,
                32: 1.4
            },
            10: {
                5: 1.4,
                2: 1.4,
                3: 1.4,
                6: 1.4,
                1: 1.4,
                12: 1.4,
                16: 1.4,
                19: 1.4,
                25: 1.4,
                27: 1.4,
                28: 1.4,
                29: 1.4,
                34: 1.4,
                35: 1.4,
                32: 1.4
            },
            12: {
                5: 1.4,
                2: 1.4,
                3: 1.4,
                6: 1.4,
                10: 1.4,
                1: 1.4,
                16: 1.4,
                19: 1.4,
                25: 1.4,
                27: 1.4,
                28: 1.4,
                29: 1.4,
                34: 1.4,
                35: 1.4,
                32: 1.4
            },
            16: {
                5: 1.4,
                2: 1,
                3: 1,
                6: 1.4,
                10: 1,
                12: 1,
                1: 1.4,
                19: 1.7,
                25: 1.7,
                27: 2,
                28: 1.8,
                29: 2,
                34: 1,
                35: 1.5,
                32: 1.7
            },
            19: {
                5: 1,
                2: 1,
                3: 1,
                6: 1,
                10: 1,
                12: 1,
                16: 1.7,
                1: 1,
                25: 1.9,
                27: 1.8,
                28: 1.7,
                29: 2,
                34: 1,
                35: 1.7,
                32: 1.9
            },
            25: {
                5: 1,
                2: 1,
                3: 1,
                6: 1,
                10: 1,
                12: 1,
                16: 1.5,
                19: 1.8,
                1: 1,
                27: 1.7,
                28: 1,
                29: 2,
                34: 1,
                35: 1.8,
                32: 2
            },
            27: {
                5: 1,
                2: 1,
                3: 1,
                6: 1,
                10: 1,
                12: 1,
                16: 2,
                19: 1.7,
                25: 1.8,
                1: 1,
                28: 1,
                29: 1.8,
                34: 1,
                35: 2,
                32: 1.8
            },
            28: {
                5: 1.4,
                2: 1.4,
                3: 1,
                6: 1.4,
                10: 1,
                12: 1,
                16: 2,
                19: 1.7,
                25: 1.4,
                27: 1.4,
                1: 1.4,
                29: 1.4,
                34: 1.4,
                35: 1.4,
                32: 1.4
            },
            29: {
                5: 1,
                2: 1,
                3: 1,
                6: 1,
                10: 1,
                12: 1,
                16: 1,
                19: 1.7,
                25: 1.9,
                27: 1.8,
                28: 1,
                1: 1,
                34: 1,
                35: 2,
                32: 2
            },
            34: {
                5: 1.4,
                2: 1.4,
                3: 1.4,
                6: 1.4,
                10: 1.4,
                12: 1.4,
                16: 1.4,
                19: 1.4,
                25: 1.4,
                27: 1.4,
                28: 1.4,
                29: 1.4,
                34: 1.4,
                35: 1.4,
                32: 1.4
            },
            35: {
                5: 1,
                2: 1,
                3: 1,
                6: 1,
                10: 1,
                12: 1,
                16: 1,
                19: 1.7,
                25: 1.8,
                27: 2,
                28: 1,
                29: 2,
                34: 1,
                1: 1,
                32: 2
            },
            32: {
                5: 1,
                2: 1,
                3: 1,
                6: 1,
                10: 1,
                12: 1,
                16: 1.4,
                19: 1.7,
                25: 1.9,
                27: 1.8,
                28: 1.4,
                29: 2,
                34: 1,
                35: 2,
            },
        }

        self.result_information = []

    def get_position_category(self, position_id: int) -> str:
        for category, positions in self.position_categories.items():
            if position_id in positions:
                return category
        return 'unknown'

    def calculate_player_probability(self, player_id: int, position_id: int,
                                     last_11_games: List[Dict],
                                     opponent_id: Optional[int] = None) -> float:
        if not last_11_games:
            return 0.0

        total_matches = len(last_11_games)
        matches_played = 0
        matches_on_position = 0
        all_positions = set()
        last_4_games_flags = []

        for i, game in enumerate(last_11_games):
            played_in_this_game = False

            for placement_key in ['home_club_placement', 'away_club_placement']:
                placement = game.get(placement_key, [])

                for line in placement:
                    for player_data in line:
                        if player_data.get('id') == player_id:
                            played_in_this_game = True
                            actual_pos = player_data.get('position_id')
                            all_positions.add(actual_pos)

                            matches_played += 1
                            if position_id in CURRENT_POSITION_MAP.get(actual_pos, []):
                                matches_on_position += 1
                            break
                    if played_in_this_game:
                        break

            if i < 4:
                last_4_games_flags.append(played_in_this_game)

        if matches_played == 0:
            return 0.0

        p1 = (matches_played / total_matches) * 100
        p2 = (matches_on_position / matches_played) * 100

        base_prob = (p1 + p2) / 2
        multiplier = 1.0


        if matches_played >= 9 and len(all_positions) >= 2:
            multiplier *= 1.85

        if len(last_4_games_flags) == 4 and all(last_4_games_flags):
            multiplier *= 1.85

        final_prob = round(min(base_prob * multiplier, 100), 2)
        return final_prob

    def has_player_ever_played_position(self, player_id: int, position_id: int,
                                        last_11_games: List[Dict]) -> bool:
        for game in last_11_games:
            for placement_key in ['home_club_placement', 'away_club_placement']:
                placement = game.get(placement_key, [])

                for line in placement:
                    for player_data in line:
                        if (player_data.get('id') == player_id and
                                player_data.get('position_id') == position_id):
                            return True
        return False

    def is_player_always_goalkeeper(self, player_id: int,
                                    last_11_games: List[Dict]) -> bool:
        positions_played = set()

        for game in last_11_games:
            for placement_key in ['home_club_placement', 'away_club_placement']:
                placement = game.get(placement_key, [])

                for line in placement:
                    for player_data in line:
                        if player_data.get('id') == player_id:
                            positions_played.add(player_data.get('position_id'))

        return len(positions_played) == 1 and 11 in positions_played

    def apply_position_penalties(self, player_id: int, position_id: int,
                                 last_11_games: List[Dict]) -> Tuple[float, float]:
        individual_prob = self.calculate_player_probability(
            player_id, position_id, last_11_games
        )
        player = Player.objects.annotate(
            fullname=Concat(F('surname'), Value(' '), F('name'))
        ).get(id=player_id)

        print(f"Вероятность игрока {player_id}) {player.fullname}: {individual_prob}")
        self.result_information.append(
            {
                "type": TypeInfo.player.value,
                "player": {
                    "id": player_id,
                    "name": player.fullname
                },
                "probability": individual_prob,
            }
        )

        line_multiplier = 1.0

        if position_id == 11 and not self.is_player_always_goalkeeper(player_id, last_11_games):
            return 0.0, 0.0

        if position_id != 11 and self.is_player_always_goalkeeper(player_id, last_11_games):
            individual_prob = 0.0
            line_multiplier = 0.1

        elif not self.has_player_ever_played_position(player_id, position_id, last_11_games):
            line_multiplier = 0.7

        return individual_prob, line_multiplier

    def calculate_line_probability(self, line_players: List[Dict],
                                   last_11_games: List[Dict]) -> Tuple[float, int]:

        if not line_players:
            return 0.0, 0

        individual_probs = []
        line_multiplier = 1.0
        weak_players_count = 0
        best_player_probs = []
        count_best_players = 0
        best_player_bonus = 0.0

        for player_data in line_players:
            player_id = player_data['id']
            position_id = player_data['position_id']

            individual_prob, multiplier = self.apply_position_penalties(
                player_id, position_id, last_11_games
            )

            individual_probs.append(individual_prob)
            line_multiplier *= multiplier

            if individual_prob < 30:
                weak_players_count += 1

            if individual_prob >= 90:
                best_player_probs.append(individual_prob)

                for player in range(len(best_player_probs)):
                    count_best_players += 1
                if count_best_players == 1:
                    best_player_bonus = 5.0
                elif count_best_players == 2:
                    best_player_bonus = 10.0
                elif count_best_players == 3:
                    best_player_bonus = 15.0

        avg_prob = sum(individual_probs) / len(individual_probs)
        line_probability = avg_prob * line_multiplier + best_player_bonus

        final_line_probability = round(max(0.0, min(100.0, line_probability)), 2)

        print(f"Вероятность линии: {final_line_probability}")
        print(f"Бонус за сильных в линии: {best_player_bonus}")
        print(f"Сильных игроков в линии: {count_best_players}")
        self.result_information.append(
            {
                "type": TypeInfo.line.value,
                "probability": final_line_probability,
                "best_player_bonus": best_player_bonus,
                "count_best_players": count_best_players,
            }
        )

        return final_line_probability, weak_players_count

    def get_formation_from_placement(self, placement: List[List[Dict]]) -> str:
        if not placement:
            return "unknown"

        formation_counts = []

        for line in placement:
            if line:
                formation_counts.append(len(line))

        if formation_counts and formation_counts[0] == 1:
            formation_counts = formation_counts[1:]

        return "-".join(map(str, formation_counts))

    def calculate_rotation_factor(self, current_lineup: List[int],
                                  previous_lineups: List[List[int]]) -> float:
        if len(previous_lineups) < 2:
            return 0.0

        total_changes = 0
        comparisons = 0

        for i in range(len(previous_lineups) - 1):
            prev_set = set(previous_lineups[i])
            next_set = set(previous_lineups[i + 1])
            changes = len(prev_set ^ next_set)
            total_changes += changes
            comparisons += 1

        avg_changes = total_changes / comparisons if comparisons > 0 else 0

        last_lineup_set = set(previous_lineups[-1])
        current_set = set(current_lineup)
        current_changes = len(last_lineup_set ^ current_set)

        change_diff = abs(current_changes - avg_changes)

        if change_diff == 1:
            return -5.0
        elif change_diff == 2:
            return -10.0
        elif current_changes > avg_changes:
            return -3.0 * (current_changes - avg_changes)
        elif current_changes < avg_changes:
            return min(2.0 * (avg_changes - current_changes), 6.0)

        return 0.0



    def calculate_squad_probability(self, proposed_squad: List[List[Dict]],
                                    last_11_games: List[Dict],
                                    club_id: int,
                                    previous_lineups: Optional[List[List[int]]] = None) -> float:
        if not proposed_squad:
            return 0.0

        line_probabilities = []
        total_weak_players = 0
        field_player_in_goal = False

        for line in proposed_squad:
            if not line:
                continue

            line_prob, weak_count = self.calculate_line_probability(line, last_11_games)

            line_probabilities.append(line_prob)

            total_weak_players += weak_count
            for player_data in line:
                if (player_data.get('position_id') == 11 and
                        not self.is_player_always_goalkeeper(player_data['id'], last_11_games)):
                    field_player_in_goal = True
                    break

        if field_player_in_goal:
            return round(max(0.0, sum(line_probabilities) / len(line_probabilities) * 0.2), 2)

        weak_lines = sum(1 for prob in line_probabilities if prob < 20)
        if weak_lines >= 2:
            return 0.0

        avg_line_probability = sum(line_probabilities) / len(line_probabilities)

        probability_with_formation = (avg_line_probability)

        rotation_adjustment = 0.0
        if previous_lineups:
            current_lineup = [player_data['id'] for line in proposed_squad for player_data in line]
            rotation_adjustment = self.calculate_rotation_factor(current_lineup, previous_lineups)

        lineup_bonus = 0.0
        current_lineup_set = {
            player_data['id']
            for line in proposed_squad
            for player_data in line
            if isinstance(player_data, dict) and 'id' in player_data
        }

        for game in last_11_games[:3]:
            for placement_key in ['home_club_placement', 'away_club_placement']:
                placement = game.get(placement_key, [])
                past_lineup = {
                    player['id']
                    for line in placement
                    for player in line
                    if isinstance(player, dict) and 'id' in player
                }

                if len(past_lineup) == 11 and len(current_lineup_set & past_lineup) == 11:
                    home_id = game['home_club_id']
                    away_id = game['away_club_id']
                    opponent_id = away_id if home_id == club_id else home_id
                    was_home = home_id == club_id

                    goals_for = game['home_score'] if was_home else game['away_score']
                    goals_against = game['away_score'] if was_home else game['home_score']

                    result_diff = goals_for - goals_against
                    match_result = (
                        'win' if result_diff > 0 else
                        'draw' if result_diff == 0 else
                        'loss'
                    )

                    importance_dict = self.rivalry_importance_by_club.get(club_id, {})
                    importance = importance_dict.get(opponent_id, 1.0)

                    if importance > 1.6:
                        if match_result == 'win':
                            lineup_bonus = 15.0
                        elif match_result == 'draw':
                            lineup_bonus = 10.0
                        elif match_result == 'loss':
                            if abs(result_diff) <= 1:
                                lineup_bonus = 0.0
                            else:
                                lineup_bonus = -10.0

                    elif importance == 1.4:
                        if match_result == 'win':
                            lineup_bonus = 10.0
                        elif match_result == 'draw':
                            lineup_bonus = 5.0
                        elif match_result == 'loss':
                            if abs(result_diff) <= 1:
                                lineup_bonus = -3.0
                            else:
                                lineup_bonus = -5.0

                    else:
                        if match_result == 'win':
                            lineup_bonus = 7.0
                        elif match_result == 'draw':
                            lineup_bonus = -5
                        else:
                            lineup_bonus = -10.0
                    break

        all_player_probs = []
        for line in proposed_squad:
            if not line:
                continue
            for player_data in line:
                player_id = player_data['id']
                position_id = player_data['position_id']
                prob = self.calculate_player_probability(player_id, position_id, last_11_games)
                all_player_probs.append(prob)

        low_confidence_players = sum(1 for p in all_player_probs if p < 30)

        low_confidence_penalty = 0.0
        if low_confidence_players == 2:
            low_confidence_penalty = 20.0
        elif low_confidence_players >= 3:
            low_confidence_penalty = 30.0
        elif low_confidence_players == 1:
            low_confidence_penalty = 10.0


        final_probability = probability_with_formation + rotation_adjustment + lineup_bonus - low_confidence_penalty
        print(f"Бонус за состав: {lineup_bonus}")
        print(f"Слабых линий: {weak_lines}")
        print(f"Фактор ротации: {rotation_adjustment}")
        print(f"Снижение за неподходящих/новых игроков: {low_confidence_penalty}")
        self.result_information.append(
            {
                "type": TypeInfo.other.value,
                "probability": None,
                "lineup_bonus": lineup_bonus,
                "weak_lines": weak_lines,
                "rotation_adjustment": rotation_adjustment,
                "low_confidence_penalty": low_confidence_penalty,
            }
        )

        return round(max(0.0, min(95.0, final_probability)), 2)

    def get_probability(self, game_id: int, club_id: int, proposed_squad: list) -> dict:
        games = Game.objects.filter(
            Q(home_club_id=club_id) | Q(away_club_id=club_id),
            is_finished=True,
            id__lt=game_id
        ).order_by('-game_date')[:11]

        last_11_games = []
        for game in games:
            last_11_games.append({
                'home_club_id': game.home_club_id,
                'away_club_id': game.away_club_id,
                'home_club_placement': game.home_club_placement,
                'away_club_placement': game.away_club_placement,
                'away_score': game.away_score,
                'home_score': game.home_score,
            })

        probability = self.calculate_squad_probability(
            proposed_squad, last_11_games, club_id
        )
        print(probability)

        return {
            "probability": probability,
            "info": self.result_information,
        }
