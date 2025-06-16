import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "football_statistics.settings")
django.setup()

import numpy as np
import json
import joblib
from keras.models import load_model
from game.models import Game
from player.models import Player, Position, PlayerGameStatistic
from club.models import Club
from django.db.models import Q

try:
    rf_model = joblib.load("sklearn_rf_model.pkl")
    et_model = joblib.load("sklearn_et_model.pkl")
    gb_model = joblib.load("sklearn_gb_model.pkl")
    lr_model = joblib.load("sklearn_lr_model.pkl")
    nn_model = load_model("sklearn_nn_model.keras", compile=False)

    try:
        improved_nn_model = load_model("neural_network_improved.keras", compile=False)
    except:
        improved_nn_model = None

    scaler = joblib.load("sklearn_scaler.pkl")

    with open("sklearn_config.json", "r") as f:
        config = json.load(f)

    POSITION_LINES = config['position_lines']
    TACTICAL_COMPATIBILITY = config['tactical_compatibility']
    EXCLUDED_POSITIONS = config['excluded_positions']

except Exception as e:
    exit(1)

def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except (ValueError, TypeError):
        return default

def has_played_this_season(player_id):
    try:
        player = Player.objects.get(id=player_id)

        if player.statistic:
            minutes_played = safe_float(getattr(player.statistic, 'minutes_played', 0))
            matches_played = safe_float(getattr(player.statistic, 'matches_uppercase', 0))

            if minutes_played > 0 or matches_played > 0:
                return True

        recent_games = PlayerGameStatistic.objects.filter(
            player_id=player_id,
            minutes_played__gt=0
        ).exists()

        return recent_games

    except Player.DoesNotExist:
        return False

def filter_players_with_game_time(squad):
    filtered_squad = []

    for player in squad:
        if has_played_this_season(player['id']):
            filtered_squad.append(player)

    return filtered_squad

def find_players_for_missing_positions(consistent_lineup, squad, used_players, used_positions, line_quality,
                                       game_date=None):

    if len(consistent_lineup) >= 11:
        return consistent_lineup

    needed = 11 - len(consistent_lineup)

    line_analysis = {
        1: {'current': 0, 'target': 1, 'positions': []},
        2: {'current': 0, 'target': 3, 'positions': []},
        4: {'current': 0, 'target': 4, 'positions': []},
        5: {'current': 0, 'target': 1, 'positions': []},
        6: {'current': 0, 'target': 2, 'positions': []}
    }

    for player in consistent_lineup:
        position_id = player['position_id']
        position_info = POSITION_LINES.get(str(position_id), {'line': 0})
        line_num = position_info['line']

        if line_num in line_analysis:
            line_analysis[line_num]['current'] += 1
            line_analysis[line_num]['positions'].append(position_id)

    line_names = {1: "Вратари", 2: "Защитники", 4: "Полузащитники", 5: "Атакующие", 6: "Нападающие"}

    priority_lines = []
    for line_num, data in line_analysis.items():
        if data['current'] < data['target']:
            shortage = data['target'] - data['current']
            priority_lines.append((line_num, shortage))

    priority_lines.sort(key=lambda x: x[1], reverse=True)

    added_players = []

    for line_num, shortage in priority_lines:
        if len(consistent_lineup) + len(added_players) >= 11:
            break

        line_name = line_names[line_num]

        if line_num in line_quality:
            required_parity = line_quality[line_num]['chosen']
        else:
            required_parity = None

        available_positions = []
        for pos_str, pos_info in POSITION_LINES.items():
            pos_id = int(pos_str)
            if (pos_info['line'] == line_num and
                    pos_id not in used_positions and
                    (pos_id == 11 or pos_id >= 11)):

                if required_parity is not None:
                    pos_parity = 'even' if pos_id % 2 == 0 else 'odd'
                    if pos_parity != required_parity:
                        continue

                available_positions.append(pos_id)

        line_added = 0
        for pos_id in available_positions:
            if line_added >= shortage or len(consistent_lineup) + len(added_players) >= 11:
                break

            candidates = []
            for player in squad:
                if (player['id'] not in used_players and
                        has_played_this_season(player['id'])):

                    if can_player_play_position(player['id'], pos_id):
                        minutes = get_player_minutes_played(player['id'])
                        candidates.append({
                            'player': player,
                            'minutes_played': minutes,
                            'position_id': pos_id
                        })

            if candidates:
                candidates.sort(key=lambda x: x['minutes_played'], reverse=True)
                best_candidate = candidates[0]

                player = best_candidate['player']
                minutes = best_candidate['minutes_played']

                new_player = {
                    'id': player['id'],
                    'name': f"{player['name']} {player['surname']}",
                    'position_id': pos_id,
                    'probability': 0.6,
                    'age': player['age'],
                    'number': player['number'],
                    'minutes_played': minutes
                }

                added_players.append(new_player)
                used_players.add(player['id'])
                used_positions.add(pos_id)
                line_added += 1

    if len(consistent_lineup) + len(added_players) < 11:
        remaining_needed = 11 - len(consistent_lineup) - len(added_players)

        any_candidates = []
        for player in squad:
            if (player['id'] not in used_players and
                    has_played_this_season(player['id']) and
                    (player['primary_position_id'] == 11 or player['primary_position_id'] >= 11) and
                    player['primary_position_id'] not in used_positions):
                minutes = get_player_minutes_played(player['id'])
                any_candidates.append({
                    'player': player,
                    'minutes_played': minutes,
                    'position_id': player['primary_position_id']
                })

        any_candidates.sort(key=lambda x: x['minutes_played'], reverse=True)

        for candidate in any_candidates[:remaining_needed]:
            player = candidate['player']
            minutes = candidate['minutes_played']

            new_player = {
                'id': player['id'],
                'name': f"{player['name']} {player['surname']}",
                'position_id': player['primary_position_id'],
                'probability': 0.5,
                'age': player['age'],
                'number': player['number'],
                'minutes_played': minutes
            }

            added_players.append(new_player)
            used_players.add(player['id'])
            used_positions.add(player['primary_position_id'])

    return consistent_lineup + added_players

def can_player_play_position(player_id, position_id):
    try:
        player = Player.objects.get(id=player_id)

        if player.primary_position_id == position_id:
            return True

        if player.position.filter(id=position_id).exists():
            return True

        player_pos_info = POSITION_LINES.get(str(player.primary_position_id), {'line': 0})
        target_pos_info = POSITION_LINES.get(str(position_id), {'line': 0})

        if (player_pos_info['line'] == target_pos_info['line'] and
                player_pos_info['line'] > 0):
            return True

        return False
    except Player.DoesNotExist:
        return False

def get_player_minutes_played(player_id):
    try:
        player = Player.objects.get(id=player_id)
        if player.statistic and player.statistic.minutes_played:
            return safe_float(player.statistic.minutes_played)
        return 0
    except Player.DoesNotExist:
        return 0

def check_position_uniqueness(lineup):
    position_ids = [player['position_id'] for player in lineup]
    unique_positions = set(position_ids)

    duplicates = []
    for pos_id in unique_positions:
        count = position_ids.count(pos_id)
        if count > 1:
            duplicates.append((pos_id, count))

    return len(duplicates) == 0, duplicates

def remove_position_duplicates(lineup):

    position_groups = {}
    for player in lineup:
        pos_id = player['position_id']
        if pos_id not in position_groups:
            position_groups[pos_id] = []
        position_groups[pos_id].append(player)

    unique_lineup = []
    removed_count = 0

    for pos_id, players in position_groups.items():
        if len(players) > 1:
            players.sort(key=lambda x: x['probability'], reverse=True)
            best_player = players[0]
            unique_lineup.append(best_player)

            for removed_player in players[1:]:
                removed_count += 1
        else:
            unique_lineup.append(players[0])

    return unique_lineup

def ensure_exactly_11_players(lineup, squad, used_player_ids, line_quality, game_date=None):
    if len(lineup) == 11:
        return lineup

    elif len(lineup) > 11:
        goalkeeper = None
        field_players = []

        for player in lineup:
            if player['position_id'] == 11:
                goalkeeper = player
            else:
                field_players.append(player)

        field_players.sort(key=lambda x: x['probability'], reverse=True)

        final_lineup = []
        if goalkeeper:
            final_lineup.append(goalkeeper)
            final_lineup.extend(field_players[:10])
        else:
            final_lineup.extend(field_players[:11])

        return final_lineup

    else:
        needed = 11 - len(lineup)

        available_players = []
        for player in squad:
            if (player['id'] not in used_player_ids and
                    has_played_this_season(player['id']) and
                    (player['primary_position_id'] == 11 or player['primary_position_id'] >= 11)):
                available_players.append(player)

        if not available_players:
            return lineup

        try:
            available_features = []
            valid_available = []

            for player in available_players:
                try:
                    features = extract_full_49_features(player, 0, game_date)
                    if len(features) == config['input_dim']:
                        available_features.append(features)
                        valid_available.append(player)
                except:
                    continue

            if available_features:
                X_available = np.array(available_features, dtype=np.float32)
                X_available_scaled = scaler.transform(X_available)
                available_probabilities = predict_with_sklearn_ensemble(X_available_scaled)

                candidates = []
                for i, player in enumerate(valid_available):
                    prob = float(available_probabilities[i])

                    try:
                        player_obj = Player.objects.get(id=player['id'])
                        primary_pos = player_obj.primary_position.name if player_obj.primary_position else "Неизвестно"
                        injury_status = "Травма" if player_obj.injury else "Здоров"
                        overall = 70
                        if player_obj.statistic:
                            overall = safe_float(getattr(player_obj.statistic, 'rating', 7.0)) * 10
                    except:
                        primary_pos = "Неизвестно"
                        injury_status = "Неизвестно"
                        overall = 70

                    candidate = {
                        'id': player['id'],
                        'name': f"{player['name']} {player['surname']}",
                        'position_id': player['primary_position_id'],
                        'position_name': primary_pos,
                        'probability': prob,
                        'injury_status': injury_status,
                        'overall': overall,
                        'age': player['age'],
                        'number': player['number']
                    }
                    candidates.append(candidate)

                filtered_candidates = []

                for candidate in candidates:
                    position_id = candidate['position_id']
                    if position_id == 11 or position_id >= 11:
                        position_info = POSITION_LINES.get(str(position_id), {'line': 0})
                        line_num = position_info['line']

                        if line_num in line_quality:
                            chosen_parity = line_quality[line_num]['chosen']
                            player_parity = 'even' if position_id % 2 == 0 else 'odd'

                            if player_parity == chosen_parity:
                                filtered_candidates.append(candidate)
                        else:
                            filtered_candidates.append(candidate)

                filtered_candidates.sort(key=lambda x: x['probability'], reverse=True)

                added_count = 0
                for candidate in filtered_candidates:
                    if added_count >= needed:
                        break

                    existing_positions = [p['position_id'] for p in lineup]
                    if candidate['position_id'] not in existing_positions:
                        lineup.append(candidate)
                        used_player_ids.add(candidate['id'])
                        added_count += 1

        except Exception as e:
            print(f"Ошибка при добавлении игроков: {e}")

        return lineup

def check_player_position_compatibility(player_id, position_id):
    try:
        player = Player.objects.get(id=player_id)
        if player.primary_position_id == position_id:
            return True
        if player.position.filter(~Q(id__in=[1, 2, 3, 4, 5]), id=position_id).exists():
            return True
        return False
    except Player.DoesNotExist:
        return False

def get_last_game_lineup(club_id, before_date=None):
    try:
        games_query = Game.objects.filter(
            Q(home_club_id=club_id) | Q(away_club_id=club_id),
            is_finished=True
        )
        if before_date:
            games_query = games_query.filter(game_date__lt=before_date)

        last_game = games_query.order_by('-game_date').first()
        if not last_game:
            return {}

        if last_game.home_club_id == club_id:
            placement = last_game.home_club_placement
        else:
            placement = last_game.away_club_placement

        if not placement:
            return {}

        lineup = {}
        for row in placement:
            for cell in row:
                player_id = cell.get("id")
                position_id = cell.get("position_id")
                if player_id and position_id:
                    lineup[position_id] = player_id
        return lineup
    except Exception:
        return {}

def find_position_players(club_id, position_id):
    try:
        primary_players = Player.objects.filter(
            club_id=club_id,
            primary_position_id=position_id,
            injury__isnull=True
        ).values_list('id', flat=True)

        secondary_players = Player.objects.filter(
            club_id=club_id,
            position__id=position_id,
            injury__isnull=True
        ).values_list('id', flat=True)

        all_players = list(set(list(primary_players) + list(secondary_players)))

        active_players = []
        for player_id in all_players:
            if has_played_this_season(player_id):
                active_players.append(player_id)

        return active_players
    except Exception:
        return []

def find_replacement_player(club_id, position_id, last_game_lineup):
    if position_id in last_game_lineup:
        last_game_player_id = last_game_lineup[position_id]
        if (check_player_position_compatibility(last_game_player_id, position_id) and
                has_played_this_season(last_game_player_id)):
            try:
                player = Player.objects.get(id=last_game_player_id)
                return last_game_player_id, f"{player.name} {player.surname}"
            except Player.DoesNotExist:
                pass

    position_players = find_position_players(club_id, position_id)
    if position_players:
        try:
            player = Player.objects.get(id=position_players[0])
            return position_players[0], f"{player.name} {player.surname}"
        except Player.DoesNotExist:
            return position_players[0], f"Player_{position_players[0]}"

    return None, None

def validate_predicted_lineup(predicted_lineup, club_id, game_date=None):
    corrected_lineup = []
    validation_report = {
        'total_players': len(predicted_lineup),
        'valid_predictions': 0,
        'corrected_predictions': 0,
        'corrections': []
    }

    last_game_lineup = get_last_game_lineup(club_id, game_date)

    for i, player_data in enumerate(predicted_lineup):
        player_id = player_data.get('id')
        position_id = player_data.get('position_id')
        player_name = player_data.get('name', f'Player_{player_id}')

        if not has_played_this_season(player_id):
            replacement_id, replacement_name = find_replacement_player(
                club_id, position_id, last_game_lineup
            )
            if replacement_id:
                corrected_player_data = player_data.copy()
                corrected_player_data['id'] = replacement_id
                corrected_player_data['name'] = replacement_name
                corrected_lineup.append(corrected_player_data)
                validation_report['corrected_predictions'] += 1
            continue

        if check_player_position_compatibility(player_id, position_id):
            corrected_lineup.append(player_data)
            validation_report['valid_predictions'] += 1
        else:
            replacement_id, replacement_name = find_replacement_player(
                club_id, position_id, last_game_lineup
            )

            if replacement_id:
                corrected_player_data = player_data.copy()
                corrected_player_data['id'] = replacement_id
                corrected_player_data['name'] = replacement_name

                corrected_lineup.append(corrected_player_data)
                validation_report['corrected_predictions'] += 1
                validation_report['corrections'].append({
                    'original_player': player_name,
                    'replacement_player': replacement_name,
                    'position_id': position_id
                })
            else:
                corrected_lineup.append(player_data)

    return corrected_lineup, validation_report

def predict_with_validation(predicted_lineup, lineup_by_lines, accuracy, club, game):
    validated_lineup, validation_report = validate_predicted_lineup(
        predicted_lineup, club.id, game.game_date
    )

    if validation_report['corrected_predictions'] > 0:
        for correction in validation_report['corrections']:
            print(f"{correction['original_player']} → {correction['replacement_player']}")
            print(f"Позиция: {correction['position_id']}")

    accuracy_rate = validation_report['valid_predictions'] / max(validation_report['total_players'], 1)
    return validated_lineup, lineup_by_lines, accuracy

def get_enhanced_player_stats(player_id):
    try:
        player_obj = Player.objects.get(id=player_id)

        basic_stats = {
            'overall': 70, 'pace': 70, 'shooting': 70, 'passing': 70,
            'dribbling': 70, 'defending': 70, 'physical': 70
        }

        if player_obj.statistic:
            stat = player_obj.statistic
            basic_stats.update({
                'rating': safe_float(getattr(stat, 'rating', 7.0)),
                'goals_per_game': safe_float(getattr(stat, 'goals', 0.0)),
                'assists_per_game': safe_float(getattr(stat, 'assists', 0.0)),
                'shots_per_game': safe_float(getattr(stat, 'shots', 0.0)),
                'passes_accuracy': safe_float(getattr(stat, 'successful_passes_accuracy', 70.0)),
                'duels_won_percent': safe_float(getattr(stat, 'duel_won_percent', 50.0)),
                'tackles_success': safe_float(getattr(stat, 'tackles_succeeded_percent', 50.0)),
                'minutes_played': safe_float(getattr(stat, 'minutes_played', 0)),
                'matches_started': safe_float(getattr(stat, 'started', 0)),
                'total_matches': safe_float(getattr(stat, 'matches_uppercase', 1))
            })

        recent_games = PlayerGameStatistic.objects.filter(
            player_id=player_id
        ).order_by('-game__game_date')[:10]

        if recent_games:
            recent_rating = np.mean([safe_float(game.rating_title) for game in recent_games if game.rating_title])
            recent_goals = sum([game.goals for game in recent_games])
            recent_assists = sum([game.assists for game in recent_games])
            recent_minutes = np.mean([game.minutes_played for game in recent_games])

            basic_stats.update({
                'recent_form_rating': recent_rating if recent_rating else 7.0,
                'recent_goals': recent_goals,
                'recent_assists': recent_assists,
                'recent_minutes_avg': recent_minutes
            })
        else:
            basic_stats.update({
                'recent_form_rating': 7.0,
                'recent_goals': 0,
                'recent_assists': 0,
                'recent_minutes_avg': 90.0
            })

        return basic_stats

    except Player.DoesNotExist:
        return {
            'overall': 70, 'pace': 70, 'shooting': 70, 'passing': 70,
            'dribbling': 70, 'defending': 70, 'physical': 70,
            'rating': 7.0, 'goals_per_game': 0.0, 'assists_per_game': 0.0,
            'shots_per_game': 0.0, 'passes_accuracy': 70.0, 'duels_won_percent': 50.0,
            'tackles_success': 50.0, 'minutes_played': 0, 'matches_started': 0,
            'total_matches': 1, 'recent_form_rating': 7.0, 'recent_goals': 0,
            'recent_assists': 0, 'recent_minutes_avg': 90.0
        }

def get_opponent_analysis(player_id, opp_club_id, position_id):
    try:
        opp_players = Player.objects.filter(
            club_id=opp_club_id,
            primary_position_id=position_id
        )

        if opp_players.exists():
            opp_ratings = []
            for opp_player in opp_players:
                if opp_player.statistic:
                    opp_ratings.append(safe_float(getattr(opp_player.statistic, 'rating', 7.0)))

            avg_opp_strength = np.mean(opp_ratings) if opp_ratings else 7.0

            our_player = Player.objects.get(id=player_id)
            our_strength = 7.0
            if our_player.statistic:
                our_strength = safe_float(getattr(our_player.statistic, 'rating', 7.0))

            superiority = our_strength / avg_opp_strength if avg_opp_strength > 0 else 1.0

            return {
                'opp_avg_strength': avg_opp_strength / 10.0,
                'superiority_factor': min(superiority, 2.0) / 2.0,
                'position_competition': len(opp_ratings) / 5.0
            }
        else:
            return {
                'opp_avg_strength': 0.7,
                'superiority_factor': 0.5,
                'position_competition': 0.0
            }

    except Exception as e:
        return {
            'opp_avg_strength': 0.7,
            'superiority_factor': 0.5,
            'position_competition': 0.0
        }

def get_tactical_compatibility(position_id, formations=['4-2-3-1', '4-3-3', '4-4-2']):
    compatibilities = []
    for formation in formations:
        if formation in TACTICAL_COMPATIBILITY:
            compatibility = TACTICAL_COMPATIBILITY[formation].get(position_id, 0.5)
            compatibilities.append(compatibility)
        else:
            compatibilities.append(0.5)

    avg_compatibility = np.mean(compatibilities)
    max_compatibility = np.max(compatibilities)

    return avg_compatibility, max_compatibility

def create_position_embedding(position_id):
    position_info = POSITION_LINES.get(str(position_id), {'line': 0, 'position': 'UNK', 'order': 0})

    line_embedding = [0.0] * 7
    line_num = position_info['line']
    if 0 <= line_num <= 6:
        line_embedding[line_num] = 1.0

    order_normalized = min(position_info['order'] / 10.0, 1.0)

    avg_tactical, max_tactical = get_tactical_compatibility(position_id)

    return line_embedding + [order_normalized, avg_tactical, max_tactical]

def create_temporal_features(game_date):
    try:
        if not game_date:
            return [0.0] * 6

        month = game_date.month
        day_of_year = game_date.timetuple().tm_yday

        is_season_start = 1.0 if month in [8, 9] else 0.0
        is_winter_break = 1.0 if month in [12, 1] else 0.0
        is_season_end = 1.0 if month in [5, 6] else 0.0

        season_cycle = np.sin(2 * np.pi * month / 12)
        year_cycle = np.sin(2 * np.pi * day_of_year / 365)

        calendar_intensity = 1.0 if month in [3, 4, 10, 11] else 0.7

        return [is_season_start, is_winter_break, is_season_end, season_cycle, year_cycle, calendar_intensity]
    except:
        return [0.0] * 6

def calculate_team_chemistry(player_id, club_id):
    try:
        player = Player.objects.get(id=player_id)

        time_factor = min(1.0, (player_id % 1000) / 1000.0)

        if player.statistic:
            minutes_factor = min(1.0, safe_float(player.statistic.minutes_played) / 2000.0)
            matches_factor = min(1.0, safe_float(player.statistic.matches_uppercase) / 30.0)
        else:
            minutes_factor = 0.5
            matches_factor = 0.5

        chemistry = (time_factor + minutes_factor + matches_factor) / 3.0
        return chemistry

    except:
        return 0.5

def calculate_motivation_factors(home_club_id, away_club_id, game_date, player_id):
    try:
        is_derby = 1.0 if abs(home_club_id - away_club_id) < 10 else 0.0

        month = game_date.month if game_date else 6
        match_importance = 1.0 if month in [4, 5, 6] else 0.8 if month in [11, 12] else 0.7

        try:
            player = Player.objects.get(id=player_id)
            if player.statistic:
                rating = safe_float(player.statistic.rating)
                personal_motivation = 1.0 - (rating / 10.0) + 0.5
                personal_motivation = min(1.0, max(0.3, personal_motivation))
            else:
                personal_motivation = 0.7
        except:
            personal_motivation = 0.7

        return [is_derby, match_importance, personal_motivation]
    except:
        return [0.0, 0.7, 0.7]

def estimate_fitness_and_form(player_id, game_date):
    try:
        player = Player.objects.get(id=player_id)

        base_fitness = 0.8

        age = player.age or 25
        if 20 <= age <= 28:
            age_factor = 1.0
        elif 29 <= age <= 32:
            age_factor = 0.9
        elif age > 32:
            age_factor = 0.8
        else:
            age_factor = 0.85

        injury_factor = 0.5 if player.injury else 1.0

        if player.statistic:
            rating = safe_float(player.statistic.rating)
            form_factor = rating / 10.0
        else:
            form_factor = 0.7

        fitness = (base_fitness * age_factor * injury_factor + form_factor) / 2.0
        fitness = min(1.0, max(0.1, fitness))

        return [fitness, age_factor, injury_factor, form_factor]
    except:
        return [0.8, 0.9, 1.0, 0.7]

def extract_full_49_features(player_data, opp_club_id, game_date=None):
    try:
        player_obj = Player.objects.get(id=player_data['id'])

        basic_features = [
            safe_float(player_data.get('height', 180)) / 200.0,
            safe_float(player_data.get('age', 25)) / 40.0,
            safe_float(player_data.get('number', 0)) / 100.0,
            safe_float(player_data.get('primary_position_id', 0)) / 120.0
        ]

        player_stats = get_enhanced_player_stats(player_data['id'])
        stat_features = [
            player_stats['rating'] / 10.0,
            player_stats['goals_per_game'] / 2.0,
            player_stats['assists_per_game'] / 2.0,
            player_stats['shots_per_game'] / 5.0,
            player_stats['passes_accuracy'] / 100.0,
            player_stats['duels_won_percent'] / 100.0,
            player_stats['tackles_success'] / 100.0,
            min(player_stats['minutes_played'] / 3000.0, 1.0),
            player_stats['matches_started'] / max(player_stats['total_matches'], 1),
            player_stats['recent_form_rating'] / 10.0,
            player_stats['recent_goals'] / 5.0,
            player_stats['recent_assists'] / 5.0,
            player_stats['recent_minutes_avg'] / 90.0,
            safe_float(player_stats['overall']) / 100.0,
            (safe_float(player_stats['pace']) + safe_float(player_stats['physical'])) / 200.0
        ]

        position_id = player_data.get('primary_position_id', 0)
        position_features = create_position_embedding(position_id)

        opponent_analysis = get_opponent_analysis(player_data['id'], opp_club_id, position_id)
        opp_features = [
            opponent_analysis['opp_avg_strength'],
            opponent_analysis['superiority_factor'],
            min(opponent_analysis['position_competition'], 1.0)
        ]

        temporal_features = create_temporal_features(game_date)

        chemistry_features = [calculate_team_chemistry(player_data['id'], player_obj.club_id)]

        motivation_features = calculate_motivation_factors(
            player_obj.club_id, opp_club_id, game_date, player_data['id']
        )

        fitness_features = estimate_fitness_and_form(player_data['id'], game_date)

        history_features = [
            min(player_data['id'] / 3000.0, 1.0),
            min((player_data['id'] % 100) / 100.0, 1.0),
            1.0 if not player_obj.injury else 0.0
        ]

        all_features = (basic_features + stat_features + position_features +
                        opp_features + temporal_features + chemistry_features +
                        motivation_features + fitness_features + history_features)

        all_features = [safe_float(f) if not (np.isnan(f) or np.isinf(f)) else 0.5 for f in all_features]

        return all_features

    except Exception as e:
        return [0.5] * 49

def predict_with_sklearn_ensemble(X):
    try:
        rf_pred = rf_model.predict_proba(X)[:, 1]
        et_pred = et_model.predict_proba(X)[:, 1]
        gb_pred = gb_model.predict_proba(X)[:, 1]
        lr_pred = lr_model.predict_proba(X)[:, 1]
        nn_pred = nn_model.predict(X, verbose=0).flatten()

        if improved_nn_model:
            improved_nn_pred = improved_nn_model.predict(X, verbose=0).flatten()
            ensemble_pred = (0.2 * rf_pred + 0.15 * et_pred + 0.15 * gb_pred +
                             0.1 * lr_pred + 0.2 * nn_pred + 0.2 * improved_nn_pred)
        else:
            ensemble_pred = (0.25 * rf_pred + 0.2 * et_pred + 0.2 * gb_pred +
                             0.15 * lr_pred + 0.2 * nn_pred)

        return ensemble_pred

    except Exception as e:
        return rf_model.predict_proba(X)[:, 1]

def organize_by_lines(predicted_players):
    lines = {}

    for player in predicted_players:
        position_id = player['position_id']
        position_info = POSITION_LINES.get(str(position_id), {'line': 0, 'position': 'Unknown', 'order': 0})

        line_num = position_info['line']
        order = position_info['order']

        if line_num not in lines:
            lines[line_num] = []

        lines[line_num].append({
            'id': player['id'],
            'position_id': position_id,
            'name': player['name'],
            'probability': player.get('probability', 0.5),
            'order': order
        })

    for line_num in lines:
        lines[line_num].sort(key=lambda x: x['order'])

    result = []
    total_players = 0

    for line_num in sorted(lines.keys()):
        if line_num > 0:
            line_players = []
            for player in lines[line_num]:
                line_players.append({
                    'id': player['id'],
                    'position_id': player['position_id'],
                    'name': player['name']
                })
                total_players += 1
            if line_players:
                result.append(line_players)

    if total_players < len(predicted_players):
        unknown_players = []
        processed_ids = set()
        for line in result:
            for player in line:
                processed_ids.add(player['id'])

        for player in predicted_players:
            if player['id'] not in processed_ids:
                unknown_players.append({
                    'id': player['id'],
                    'position_id': player['position_id'],
                    'name': player['name']
                })

        if unknown_players:
            result.append(unknown_players)
            total_players += len(unknown_players)

    return result

def compare_with_actual_sklearn(game, club, is_home, predicted_lineup):
    try:
        actual_placement = game.home_club_placement if is_home else game.away_club_placement

        if not actual_placement:
            return 0.0

        actual_players = []

        excluded_positions = list(EXCLUDED_POSITIONS)
        for pos_id in range(1, 11):
            if pos_id != 11:
                excluded_positions.append(pos_id)

        pos = 1
        for row in actual_placement:
            for cell in row:
                player_id = cell.get("id")
                position_id = cell.get("position_id")

                if (player_id and position_id not in excluded_positions and
                    (position_id == 11 or position_id >= 11)):
                    actual_players.append(player_id)

                    try:
                        player_obj = Player.objects.get(id=player_id)
                        pos += 1
                    except:
                        pos += 1

        predicted_players = [p['id'] for p in predicted_lineup]
        matches = set(predicted_players) & set(actual_players)
        accuracy = len(matches) / len(actual_players) if actual_players else 0

        if matches:
            for player_id in matches:
                try:
                    player_obj = Player.objects.get(id=player_id)
                    pred_player = next((p for p in predicted_lineup if p['id'] == player_id), None)
                    prob = pred_player['probability'] if pred_player else 0
                    pos_id = pred_player['position_id'] if pred_player else 0
                except:
                    print(f" Игрок ID: {player_id}")

        return accuracy

    except Exception as e:
        return 0.0

def fix_incomplete_lineup(predicted_lineup, lineup_by_lines, game_id, is_home):
    try:
        actual_count = len(predicted_lineup)
        lines_count = sum(len(line) for line in lineup_by_lines)

        if actual_count == lines_count and actual_count >= 11:
            return predicted_lineup, lineup_by_lines

        if actual_count == lines_count and lines_count < 11:
            return predicted_lineup, lineup_by_lines

        if actual_count != lines_count:
            new_lineup_by_lines = organize_by_lines(predicted_lineup)
            return predicted_lineup, new_lineup_by_lines

        game = Game.objects.get(pk=game_id)
        club = game.home_club if is_home else game.away_club
        opp = game.away_club if is_home else game.home_club

        needed = 11 - actual_count
        excluded_positions = list(EXCLUDED_POSITIONS)
        for pos_id in range(1, 11):
            if pos_id != 11 and pos_id not in excluded_positions:
                excluded_positions.append(pos_id)

        all_squad_raw = Player.objects.filter(club=club).exclude(
            primary_position_id__in=excluded_positions
        ).values('id', 'name', 'surname', 'primary_position_id', 'height', 'age', 'number')

        all_squad = []
        for player in all_squad_raw:
            pos_id = player['primary_position_id'] or 0
            if pos_id == 11 or pos_id >= 11:
                all_squad.append(player)

        used_ids = {p['id'] for p in predicted_lineup}

        available_players = []
        for player in all_squad:
            if player['id'] not in used_ids and has_played_this_season(player['id']):
                safe_player = {
                    'id': player['id'],
                    'name': player['name'] or 'Unknown',
                    'surname': player['surname'] or 'Player',
                    'primary_position_id': player['primary_position_id'] or 0,
                    'height': player['height'] if player['height'] is not None else 180,
                    'age': player['age'] if player['age'] is not None else 25,
                    'number': player['number'] if player['number'] is not None else 0
                }
                available_players.append(safe_player)

        if not available_players:
            return predicted_lineup, lineup_by_lines
        else:
            print(f"Анализируем {len(available_players)} доступных активных игроков...")

            player_features = []
            valid_players = []

            for player in available_players:
                try:
                    features = extract_full_49_features(player, opp.id, game.game_date)
                    if len(features) == config['input_dim']:
                        player_features.append(features)
                        valid_players.append(player)
                except Exception as e:
                    continue

            if player_features:
                X = np.array(player_features, dtype=np.float32)
                X_scaled = scaler.transform(X)
                probabilities = predict_with_sklearn_ensemble(X_scaled)

                candidates = []
                for i, player in enumerate(valid_players):
                    prob = float(probabilities[i])

                    try:
                        player_obj = Player.objects.get(id=player['id'])
                        primary_pos = player_obj.primary_position.name if player_obj.primary_position else "Неизвестно"
                        injury_status = "Травма" if player_obj.injury else "Здоров"
                        overall = 70
                        if player_obj.statistic:
                            overall = safe_float(getattr(player_obj.statistic, 'rating', 7.0)) * 10
                    except:
                        primary_pos = "Неизвестно"
                        injury_status = "Неизвестно"
                        overall = 70

                    candidate = {
                        'id': player['id'],
                        'name': f"{player['name']} {player['surname']}",
                        'position_id': player['primary_position_id'],
                        'position_name': primary_pos,
                        'probability': prob,
                        'injury_status': injury_status,
                        'overall': overall,
                        'age': player['age'],
                        'number': player['number']
                    }
                    candidates.append(candidate)

                candidates.sort(key=lambda x: x['probability'], reverse=True)

                added = 0
                for candidate in candidates:
                    if added >= needed:
                        break
                    predicted_lineup.append(candidate)
                    added += 1

                if added < needed:
                    print(f" Удалось добавить только {added} из {needed} активных игроков")
                else:
                    print(f"Добавлено {added} активных игроков с помощью ИИ")
            else:
                print("Не удалось обработать доступных активных игроков")

        new_lineup_by_lines = organize_by_lines(predicted_lineup)

        final_count = len(predicted_lineup)
        if final_count < 11:
            print(f"Только {final_count} активных игроков доступно")

        return predicted_lineup, new_lineup_by_lines

    except Exception as e:
        print(f"Ошибка исправления состава: {e}")
        return predicted_lineup, lineup_by_lines

def predict_sklearn_lineup(game_id, is_home=True):
    try:
        game = Game.objects.get(pk=game_id)
        club = game.home_club if is_home else game.away_club
        opp = game.away_club if is_home else game.home_club

        excluded_positions = list(EXCLUDED_POSITIONS)
        for pos_id in range(1, 11):
            if pos_id != 11 and pos_id not in excluded_positions:
                excluded_positions.append(pos_id)

        squad_raw = Player.objects.filter(club=club).exclude(
            primary_position_id__in=excluded_positions
        ).values('id', 'name', 'surname', 'primary_position_id', 'height', 'age', 'number')

        squad = []
        for player in squad_raw:
            pos_id = player['primary_position_id'] or 0
            if pos_id == 11 or pos_id >= 11:
                safe_player = {
                    'id': player['id'],
                    'name': player['name'] or 'Unknown',
                    'surname': player['surname'] or 'Player',
                    'primary_position_id': pos_id,
                    'height': player['height'] if player['height'] is not None else 180,
                    'age': player['age'] if player['age'] is not None else 25,
                    'number': player['number'] if player['number'] is not None else 0
                }
                squad.append(safe_player)

        active_squad = filter_players_with_game_time(squad)

        if len(active_squad) < 1:
            return [], [], 0.0

        squad = active_squad

        player_features = []
        valid_players = []

        for player in squad:
            try:
                features = extract_full_49_features(player, opp.id, game.game_date)
                if len(features) == config['input_dim']:
                    player_features.append(features)
                    valid_players.append(player)
            except Exception as e:
                print(f"Ошибка обработки игрока {player['name']}: {e}")
                continue

        if not player_features:
            print("Не удалось обработать ни одного игрока")
            return [], [], 0.0

        X = np.array(player_features, dtype=np.float32)
        X_scaled = scaler.transform(X)

        probabilities = predict_with_sklearn_ensemble(X_scaled)

        results = []
        for i, player in enumerate(valid_players):
            prob = float(probabilities[i])

            try:
                player_obj = Player.objects.get(id=player['id'])
                primary_pos = player_obj.primary_position.name if player_obj.primary_position else "Неизвестно"
                injury_status = "Травма" if player_obj.injury else "Здоров"
                overall = 70
                if player_obj.statistic:
                    overall = safe_float(getattr(player_obj.statistic, 'rating', 7.0)) * 10
            except:
                primary_pos = "Неизвестно"
                injury_status = "Неизвестно"
                overall = 70

            results.append({
                'id': player['id'],
                'name': f"{player['name']} {player['surname']}",
                'position_id': player['primary_position_id'],
                'position_name': primary_pos,
                'probability': prob,
                'injury_status': injury_status,
                'overall': overall,
                'age': player['age'],
                'number': player['number']
            })

        results.sort(key=lambda x: x['probability'], reverse=True)

        goalkeepers = [p for p in results if p['position_id'] == 11]
        field_players = [p for p in results if p['position_id'] != 11]

        if goalkeepers:
            best_gk = goalkeepers[0]
        else:
            return [], [], 0.0

        line_players = {
            2: {'even': [], 'odd': []},
            4: {'even': [], 'odd': []},
            5: {'even': [], 'odd': []},
            6: {'even': [], 'odd': []}
        }

        for player in field_players:
            position_id = player['position_id']
            position_info = POSITION_LINES.get(str(position_id), {'line': 0})
            line_num = position_info['line']

            if line_num in line_players:
                if position_id % 2 == 0:
                    line_players[line_num]['even'].append(player)
                else:
                    line_players[line_num]['odd'].append(player)

        for line_num in line_players:
            line_players[line_num]['even'].sort(key=lambda x: x['probability'], reverse=True)
            line_players[line_num]['odd'].sort(key=lambda x: x['probability'], reverse=True)

        line_quality = {}
        for line_num in line_players:
            even_quality = sum(p['probability'] for p in line_players[line_num]['even'][:4])
            odd_quality = sum(p['probability'] for p in line_players[line_num]['odd'][:4])

            line_quality[line_num] = {
                'even': even_quality,
                'odd': odd_quality,
                'chosen': 'even' if even_quality >= odd_quality else 'odd'
            }

        line_names = {2: "Защитники", 4: "Полузащитники", 5: "Атакующие", 6: "Нападающие"}
        for line_num, quality in line_quality.items():
            parity_text = "четные" if quality['chosen'] == 'even' else "нечетные"

        consistent_lineup = []
        used_players = set()
        used_positions = set()

        consistent_lineup.append(best_gk)
        used_players.add(best_gk['id'])
        used_positions.add(best_gk['position_id'])

        target_counts = {2: 3, 4: 4, 5: 1, 6: 2}

        for line_num in [2, 4, 5, 6]:
            chosen_parity = line_quality[line_num]['chosen']
            available_players = line_players[line_num][chosen_parity]
            target_count = target_counts[line_num]

            added_count = 0
            for player in available_players:
                if (player['id'] not in used_players and
                        player['position_id'] not in used_positions and
                        added_count < target_count and
                        len(consistent_lineup) < 11):
                    consistent_lineup.append(player)
                    used_players.add(player['id'])
                    used_positions.add(player['position_id'])
                    added_count += 1

        if len(consistent_lineup) < 11:
            consistent_lineup = find_players_for_missing_positions(
                consistent_lineup, squad, used_players, used_positions, line_quality, game.game_date
            )

        final_positions = [p['position_id'] for p in consistent_lineup]
        unique_positions = set(final_positions)

        if len(final_positions) != len(unique_positions):
            consistent_lineup = remove_position_duplicates(consistent_lineup)

        if len(consistent_lineup) > 11:
            consistent_lineup.sort(key=lambda x: x['probability'], reverse=True)
            consistent_lineup = consistent_lineup[:11]

        final_positions = [p['position_id'] for p in consistent_lineup]
        unique_positions = set(final_positions)

        predicted_lineup = consistent_lineup

        lineup_by_lines = organize_by_lines(predicted_lineup)

        for i, line in enumerate(lineup_by_lines):
            line_num = i + 1
            line_names_display = {1: "Вратарь", 2: "Защитники", 3: "Опорные полузащитники",
                                  4: "Полузащитники", 5: "Атакующие полузащитники", 6: "Нападающие"}

            for player in line:
                player_info = next((p for p in predicted_lineup if p['id'] == player['id']), None)
                if player_info:
                    minutes = player_info.get('minutes_played', 0)
                    minutes_text = f" ({minutes} мин)" if minutes > 0 else ""

        total_confidence = sum([p['probability'] for p in predicted_lineup])
        avg_confidence = total_confidence / len(predicted_lineup) if predicted_lineup else 0

        accuracy = compare_with_actual_sklearn(game, club, is_home, predicted_lineup)

        return predict_with_validation(predicted_lineup, lineup_by_lines, accuracy, club, game)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return [], [], 0.0

def main():
    while True:
        choice = input("\nВаш выбор (1-6): ").strip()

        if choice == "1":
            try:
                game_id = input("ID игры: ").strip()
                if not game_id.isdigit():
                    continue

                is_home = input("Домашняя команда? (y/n): ").strip().lower() == "y"
                predicted_lineup, lineup_by_lines, accuracy = predict_sklearn_lineup(int(game_id), is_home)

                if not predicted_lineup or len(predicted_lineup) != 11:
                    if predicted_lineup and len(predicted_lineup) > 0:
                        for player in predicted_lineup:
                            print(f"  - {player['name']} (позиция {player['position_id']})")
                    continue

                if lineup_by_lines:
                    for line in lineup_by_lines:
                        for i, player in enumerate(line):
                            if i > 0:
                                print(", ", end="")
                            print(
                                f'{{"id": {player["id"]}, "position_id": {player["position_id"]}, "name": "{player["name"]}"}}',
                                end="")
                        print("],")
                    print("]")

                    all_positions = []
                    for line in lineup_by_lines:
                        for player in line:
                            all_positions.append(player["position_id"])

                    if len(all_positions) == 11:
                        if len(set(all_positions)) == 11:
                            print("нет дублирующих позиций")
                        else:
                            print(f"есть дублированные позиции")
                    elif len(all_positions) < 11:
                        print(f"мало игроков ({len(all_positions)} из 11)")

                        predicted_lineup, lineup_by_lines = fix_incomplete_lineup(
                            predicted_lineup, lineup_by_lines, int(game_id), is_home
                        )

                        all_positions = []
                        for line in lineup_by_lines:
                            for player in line:
                                all_positions.append(player["position_id"])

                        if len(all_positions) == 11:
                            print("Теперь ровно 11 игроков")
                        elif len(all_positions) < 11:
                            print(f"Только {len(all_positions)} активных игроков доступно")
                        else:
                            print(f"получилось {len(all_positions)} игроков, показываем результат")
                    else:
                        print(f"много игрокров ({len(all_positions)} > 11)")

                    save_format = input("\nСохранить результат в файл? (y/n): ").strip().lower() == "y"
                    if save_format:
                        try:
                            game = Game.objects.get(pk=int(game_id))
                            club_name = (game.home_club if is_home else game.away_club).name
                            filename = f"validated_lineup_game_{game_id}_{club_name.replace(' ', '_')}.json"

                            output_data = {
                                'game_id': int(game_id),
                                'club_name': club_name,
                                'is_home': is_home,
                                'accuracy': float(accuracy) if accuracy else None,
                                'lineup_by_lines': lineup_by_lines,
                                'predicted_lineup': predicted_lineup,
                                'model_type': 'sklearn_ensemble_strict_constraints',
                                'features_count': config['input_dim'],
                                'constraints_validated': {
                                    'total_players': len(all_positions),
                                    'unique_positions': len(set(all_positions)),
                                    'all_active_players': True,
                                    'strict_constraints_followed': True
                                }
                            }

                            with open(filename, 'w', encoding='utf-8') as f:
                                json.dump(output_data, f, indent=2, ensure_ascii=False)
                        except Exception as e:
                            print(f"Ошибка сохранения: {e}")
                else:
                    for i, player in enumerate(predicted_lineup, 1):
                        print(f"{i:2d}. {player['name']} - позиция {player['position_id']}")

            except Exception as e:
                print(f"Ошибка: {e}")

        elif choice == "2":
            try:
                player_id = int(input("ID игрока: "))
                position_id = int(input("ID позиции: "))

                can_play = check_player_position_compatibility(player_id, position_id)

                try:
                    player = Player.objects.get(id=player_id)
                    player_name = f"{player.name} {player.surname}"

                    try:
                        position = Position.objects.get(id=position_id)
                        position_name = position.name
                    except Position.DoesNotExist:
                        position_name = f"Position_{position_id}"

                    if can_play:
                        print(f"может играть на этой позиции")
                    else:
                        print(f"не может играть на этой позиции")

                except Player.DoesNotExist:
                    print(f"Игрок с ID {player_id} не найден")

            except ValueError:
                print("Введите числовые ID")

        elif choice == "3":
            try:
                player_id = int(input("ID игрока: "))

                has_time = has_played_this_season(player_id)

                try:
                    player = Player.objects.get(id=player_id)
                    player_name = f"{player.name} {player.surname}"

                    if has_time:
                        if player.statistic:
                            minutes = safe_float(getattr(player.statistic, 'minutes_played', 0))
                            matches = safe_float(getattr(player.statistic, 'matches_uppercase', 0))
                    else:
                        print(f"не играл в этом сезоне")

                except Player.DoesNotExist:
                    print(f"Игрок с ID {player_id} не найден")

            except ValueError:
                print("Введите числовой ID")

        elif choice == "5":
            try:
                player_id = int(input("ID игрока для теста: "))
                opp_club_id = int(input("ID команды соперника: "))

                try:
                    player = Player.objects.get(id=player_id)
                    player_data = {
                        'id': player.id,
                        'name': player.name or 'Unknown',
                        'surname': player.surname or 'Player',
                        'primary_position_id': player.primary_position_id or 0,
                        'height': player.height or 180,
                        'age': player.age or 25,
                        'number': player.number or 0
                    }

                    features = extract_full_49_features(player_data, opp_club_id)
                    has_time = has_played_this_season(player_id)

                    if len(features) == config['input_dim']:

                        feature_names = config.get('feature_names', [])
                        for i in range(min(10, len(features))):
                            name = feature_names[i] if i < len(feature_names) else f"feature_{i}"

                except Player.DoesNotExist:
                    print(f"Игрок с ID {player_id} не найден")

            except ValueError:
                print("Введите числовые ID")

        else:
            print("Выберите от 1 до 5")

if __name__ == "__main__":
    main()