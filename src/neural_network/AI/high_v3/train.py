import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "football_statistics.settings")
django.setup()

import numpy as np
import pandas as pd
import tensorflow as tf

import keras
from keras import layers, Model
from keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau
from tqdm import tqdm
import json
from collections import Counter
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, f1_score, accuracy_score, roc_auc_score
from sklearn.utils.class_weight import compute_class_weight
import joblib

from data_pipeline import build_raw_rows, time_split
from game.models import Game
from player.models import Player, Position, PlayerGameStatistic
from club.models import Club

COACH_POSITION_ID = 1
EXCLUDED_POSITIONS = [COACH_POSITION_ID]

POSITION_LINES = {
    11: {'line': 1, 'position': 'GK', 'order': 1},
    23: {'line': 0, 'position': 'UNK', 'order': 0},
    25: {'line': 0, 'position': 'UNK', 'order': 0},
    27: {'line': 0, 'position': 'UNK', 'order': 0},
    29: {'line': 0, 'position': 'UNK', 'order': 0},
    31: {'line': 2, 'position': 'DEF', 'order': 2},
    32: {'line': 2, 'position': 'DEF', 'order': 3},
    33: {'line': 2, 'position': 'DEF', 'order': 4},
    34: {'line': 2, 'position': 'DEF', 'order': 5},
    35: {'line': 2, 'position': 'DEF', 'order': 6},
    36: {'line': 2, 'position': 'DEF', 'order': 7},
    37: {'line': 2, 'position': 'DEF', 'order': 8},
    38: {'line': 2, 'position': 'DEF', 'order': 9},
    39: {'line': 2, 'position': 'DEF', 'order': 10},
    41: {'line': 2, 'position': 'DEF', 'order': 2},
    51: {'line': 2, 'position': 'DEF', 'order': 2},
    52: {'line': 2, 'position': 'DEF', 'order': 3},
    53: {'line': 2, 'position': 'DEF', 'order': 4},
    54: {'line': 2, 'position': 'DEF', 'order': 5},
    55: {'line': 2, 'position': 'DEF', 'order': 6},
    56: {'line': 2, 'position': 'DEF', 'order': 7},
    57: {'line': 2, 'position': 'DEF', 'order': 8},
    58: {'line': 2, 'position': 'DEF', 'order': 9},
    59: {'line': 2, 'position': 'DEF', 'order': 10},
    62: {'line': 3, 'position': 'MID', 'order': 3},
    63: {'line': 3, 'position': 'MID', 'order': 4},
    64: {'line': 3, 'position': 'MID', 'order': 5},
    65: {'line': 3, 'position': 'MID', 'order': 6},
    66: {'line': 3, 'position': 'MID', 'order': 7},
    67: {'line': 3, 'position': 'MID', 'order': 8},
    68: {'line': 3, 'position': 'MID', 'order': 9},
    71: {'line': 4, 'position': 'MID', 'order': 2},
    72: {'line': 4, 'position': 'MID', 'order': 3},
    73: {'line': 4, 'position': 'MID', 'order': 4},
    74: {'line': 4, 'position': 'MID', 'order': 5},
    75: {'line': 4, 'position': 'MID', 'order': 6},
    76: {'line': 4, 'position': 'MID', 'order': 7},
    77: {'line': 4, 'position': 'MID', 'order': 8},
    78: {'line': 4, 'position': 'MID', 'order': 9},
    79: {'line': 4, 'position': 'MID', 'order': 10},
    81: {'line': 5, 'position': 'AM', 'order': 2},
    82: {'line': 5, 'position': 'AM', 'order': 3},
    83: {'line': 5, 'position': 'AM', 'order': 4},
    84: {'line': 5, 'position': 'AM', 'order': 5},
    85: {'line': 5, 'position': 'AM', 'order': 6},
    86: {'line': 5, 'position': 'AM', 'order': 7},
    87: {'line': 5, 'position': 'AM', 'order': 8},
    88: {'line': 5, 'position': 'AM', 'order': 9},
    89: {'line': 5, 'position': 'AM', 'order': 10},
    93: {'line': 5, 'position': 'AM', 'order': 4},
    94: {'line': 5, 'position': 'AM', 'order': 5},
    95: {'line': 5, 'position': 'AM', 'order': 6},
    96: {'line': 5, 'position': 'AM', 'order': 7},
    97: {'line': 5, 'position': 'AM', 'order': 8},
    102: {'line': 6, 'position': 'FW', 'order': 3},
    103: {'line': 6, 'position': 'FW', 'order': 4},
    104: {'line': 6, 'position': 'FW', 'order': 5},
    105: {'line': 6, 'position': 'FW', 'order': 6},
    106: {'line': 6, 'position': 'FW', 'order': 7},
    107: {'line': 6, 'position': 'FW', 'order': 8},
    108: {'line': 6, 'position': 'FW', 'order': 9},
    114: {'line': 6, 'position': 'FW', 'order': 5},
    115: {'line': 6, 'position': 'FW', 'order': 6},
    116: {'line': 6, 'position': 'FW', 'order': 7},
}

TACTICAL_COMPATIBILITY = {
    "4-2-3-1": {
        11: 0.95, 32: 0.95, 34: 0.95, 36: 0.95, 38: 0.95,
        64: 0.95, 66: 0.95, 83: 0.95, 85: 0.95, 87: 0.95, 115: 0.95,
    },
    "4-3-3": {
        11: 0.95, 32: 0.95, 34: 0.95, 36: 0.95, 38: 0.95,
        73: 0.95, 75: 0.95, 77: 0.95, 103: 0.95, 105: 0.95, 107: 0.95,
    },
    "4-4-2": {
        11: 0.95, 32: 0.95, 34: 0.95, 36: 0.95, 38: 0.95,
        72: 0.95, 74: 0.95, 76: 0.95, 78: 0.95, 104: 0.95, 106: 0.95,
    },
    "3-4-3": {
        11: 0.95, 33: 0.95, 35: 0.95, 37: 0.95,
        72: 0.95, 74: 0.95, 76: 0.95, 78: 0.95,
        103: 0.95, 105: 0.95, 107: 0.95,
    },
    "3-5-2": {
        11: 0.95, 33: 0.95, 35: 0.95, 37: 0.95,
        71: 0.95, 73: 0.95, 75: 0.95, 77: 0.95, 79: 0.95,
        104: 0.95, 106: 0.95,
    },
    "5-3-2": {
        11: 0.95, 31: 0.71, 33: 0.92, 35: 0.92, 37: 0.92, 39: 0.71,
        73: 0.95, 75: 0.95, 77: 0.95, 104: 0.95, 106: 0.95,
    },
    "4-1-4-1": {
        11: 0.95, 32: 0.95, 34: 0.95, 36: 0.95, 38: 0.95, 65: 0.95,
        82: 0.95, 84: 0.95, 86: 0.95, 88: 0.95, 115: 0.95,
    },
    "5-4-1": {
        11: 0.95, 31: 0.93, 33: 0.93, 35: 0.93, 37: 0.93, 39: 0.93,
        72: 0.95, 74: 0.95, 76: 0.95, 78: 0.95, 115: 0.95,
    },
    "4-5-1": {
        11: 0.95, 32: 0.95, 34: 0.95, 36: 0.95, 38: 0.95,
        71: 0.95, 73: 0.95, 75: 0.95, 77: 0.95, 79: 0.95, 115: 0.95,
    },
    "3-4-2-1": {
        11: 0.95, 33: 0.95, 35: 0.95, 37: 0.95,
        72: 0.95, 74: 0.95, 76: 0.95, 78: 0.95,
        94: 0.95, 96: 0.95, 115: 0.95,
    },
    "4-3-1-2": {
        11: 0.95, 32: 0.94, 34: 0.94, 36: 0.94, 38: 0.94,
        63: 0.94, 65: 0.94, 67: 0.94, 85: 0.94, 104: 0.94, 106: 0.94,
    },
    "5-2-1-2": {
        11: 0.95, 32: 0.71, 34: 0.71, 36: 0.71, 38: 0.71, 55: 0.71,
        74: 0.95, 76: 0.95, 95: 0.95, 114: 0.95, 116: 0.95,
    },
    "4-1-2-3": {
        11: 0.95, 32: 0.95, 34: 0.95, 36: 0.95, 38: 0.95, 65: 0.95,
        84: 0.95, 86: 0.95, 103: 0.95, 105: 0.95, 107: 0.95,
    },
}

df = build_raw_rows()
df = df[df["placement_out_js"].apply(len) > 0].reset_index(drop=True)



def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


def is_valid_player(player_id, position_id):
    return position_id not in EXCLUDED_POSITIONS and player_id != 0 and position_id != 0


def extract_advanced_features_filtered(placement_json):
    players = []
    positions = []

    if placement_json:
        for row in placement_json:
            for cell in row:
                player_id = cell.get("id")
                position_id = cell.get("position_id")

                if player_id and position_id and is_valid_player(player_id, position_id):
                    try:
                        players.append(int(player_id))
                        positions.append(int(position_id))
                    except (ValueError, TypeError):
                        continue

    return players, positions


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
    position_info = POSITION_LINES.get(position_id, {'line': 0, 'position': 'UNK', 'order': 0})

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


def create_ultra_features_improved(club_id, opp_id, players_in_game, game_date=None):
    try:
        all_squad = Player.objects.filter(club_id=club_id).exclude(
            primary_position_id__in=EXCLUDED_POSITIONS
        )

        squad_ids = list(all_squad.values_list('id', flat=True))

        if len(squad_ids) < 11:
            return None, None

        features = []
        targets = []

        for player_id in squad_ids:
            try:
                player_obj = Player.objects.get(id=player_id)

                basic_features = [
                    safe_float(player_obj.height or 180) / 200.0,
                    safe_float(player_obj.age or 25) / 40.0,
                    safe_float(player_obj.number or 0) / 100.0,
                    safe_float(player_obj.primary_position_id or 0) / 120.0
                ]

                player_stats = get_enhanced_player_stats(player_id)
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

                position_id = player_obj.primary_position_id or 0
                position_features = create_position_embedding(position_id)

                opponent_analysis = get_opponent_analysis(player_id, opp_id, position_id)
                opp_features = [
                    opponent_analysis['opp_avg_strength'],
                    opponent_analysis['superiority_factor'],
                    min(opponent_analysis['position_competition'], 1.0)
                ]

                temporal_features = create_temporal_features(game_date)

                chemistry_features = [calculate_team_chemistry(player_id, club_id)]

                motivation_features = calculate_motivation_factors(club_id, opp_id, game_date, player_id)

                fitness_features = estimate_fitness_and_form(player_id, game_date)

                history_features = [
                    min(player_id / 3000.0, 1.0),
                    min((player_id % 100) / 100.0, 1.0),
                    1.0 if not player_obj.injury else 0.0
                ]

                all_features = (basic_features + stat_features + position_features +
                                opp_features + temporal_features + chemistry_features +
                                motivation_features + fitness_features + history_features)

                all_features = [safe_float(f) if not (np.isnan(f) or np.isinf(f)) else 0.5 for f in all_features]

                features.append(all_features)

                target = 1.0 if player_id in players_in_game else 0.0
                targets.append(target)

            except Exception as e:
                continue

        return np.array(features, dtype=np.float32), np.array(targets, dtype=np.float32)

    except Exception as e:
        return None, None


def create_enhanced_dataset():
    all_features = []
    all_targets = []
    processed_count = 0
    filtered_coaches = 0

    for _, row in tqdm(df.iterrows(), total=len(df), desc="Улучшенная обработка"):
        try:
            players, positions = extract_advanced_features_filtered(row['placement_out_js'])

            if row['placement_out_js']:
                for r in row['placement_out_js']:
                    for cell in r:
                        if cell.get("position_id") == COACH_POSITION_ID:
                            filtered_coaches += 1

            if len(players) < 5:
                continue

            features, targets = create_ultra_features_improved(
                row['club_id'], row['opp_id'], players, row.get('game_date')
            )

            if features is not None and len(features) > 0:
                all_features.append(features)
                all_targets.append(targets)
                processed_count += 1

        except Exception as e:
            continue

    return all_features, all_targets


def create_improved_neural_network(input_dim):
    inputs = layers.Input(shape=(input_dim,), name='player_features')

    x = layers.BatchNormalization(name='input_norm')(inputs)

    x1 = layers.Dense(512, name='feature_extract')(x)
    x1 = layers.BatchNormalization()(x1)
    x1 = layers.Activation('swish')(x1)
    x1 = layers.Dropout(0.3)(x1)

    attention_weights = layers.Dense(512, activation='tanh')(x1)
    attention_weights = layers.Dense(512, activation='softmax')(attention_weights)
    x2 = layers.Multiply()([x1, attention_weights])

    x3 = layers.Dense(256, activation='swish')(x2)
    x3 = layers.BatchNormalization()(x3)
    x3 = layers.Dropout(0.2)(x3)

    residual = layers.Dense(128, activation='swish')(x)

    x4 = layers.Dense(128, activation='swish')(x3)
    x4 = layers.Add()([x4, residual])
    x4 = layers.Dropout(0.1)(x4)

    output = layers.Dense(
        1,
        activation='sigmoid',
        kernel_regularizer=keras.regularizers.l1_l2(l1=1e-5, l2=1e-4)
    )(x4)

    model = Model(inputs, output, name='improved_football_ai')


    model.compile(
        optimizer=keras.optimizers.AdamW(
            learning_rate=1e-3,
            weight_decay=1e-4
        ),
        loss='binary_crossentropy',
        metrics=['accuracy', 'auc']
    )

    return model


def smart_data_augmentation(X_train, y_train, augment_ratio=0.25):
    playing_mask = y_train == 1
    playing_X = X_train[playing_mask]

    if len(playing_X) == 0:
        return X_train, y_train

    n_augmented = int(len(playing_X) * augment_ratio)
    augmented_samples = []

    for _ in range(n_augmented):
        idx = np.random.randint(0, len(playing_X))
        original = playing_X[idx].copy()

        noise_factor = 0.03
        noise = np.random.normal(0, noise_factor, original.shape)

        mask = np.random.random(original.shape) < 0.6
        augmented = original + noise * mask

        augmented = np.clip(augmented, 0, 1)
        augmented_samples.append(augmented)

    if augmented_samples:
        X_augmented = np.vstack([X_train, np.array(augmented_samples)])
        y_augmented = np.hstack([y_train, np.ones(len(augmented_samples))])

        indices = np.random.permutation(len(X_augmented))
        return X_augmented[indices], y_augmented[indices]

    return X_train, y_train


def get_advanced_callbacks():
    return [
        EarlyStopping(
            monitor='val_auc',
            patience=15,
            restore_best_weights=True,
            verbose=1,
            mode='max'
        ),
        ModelCheckpoint(
            'best_improved_model.keras',
            save_best_only=True,
            monitor='val_auc',
            mode='max',
            verbose=1
        ),
        ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.6,
            patience=8,
            min_lr=1e-7,
            verbose=1
        ),
        keras.callbacks.LearningRateScheduler(
            lambda epoch: 1e-3 * 0.5 * (1 + np.cos(np.pi * epoch / 80)),
            verbose=0
        ),
    ]


def create_sklearn_ensemble():
    rf_model = RandomForestClassifier(
        n_estimators=200,
        max_depth=15,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )

    et_model = ExtraTreesClassifier(
        n_estimators=200,
        max_depth=15,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )

    gb_model = GradientBoostingClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        random_state=42
    )

    lr_model = LogisticRegression(
        random_state=42,
        max_iter=1000
    )

    return rf_model, et_model, gb_model, lr_model


def improved_training_loop():
    from sklearn.model_selection import StratifiedKFold

    kfold = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    fold_scores = []

    for fold, (train_idx, val_idx) in enumerate(kfold.split(X_all, y_all)):

        X_fold_train, X_fold_val = X_all[train_idx], X_all[val_idx]
        y_fold_train, y_fold_val = y_all[train_idx], y_all[val_idx]

        X_fold_aug, y_fold_aug = smart_data_augmentation(X_fold_train, y_fold_train, 0.2)

        fold_model = create_improved_neural_network(X_fold_train.shape[1])

        fold_class_weights = compute_class_weight('balanced', classes=np.unique(y_fold_aug), y=y_fold_aug)
        fold_class_weight_dict = {i: weight for i, weight in enumerate(fold_class_weights)}

        fold_model.fit(
            X_fold_aug, y_fold_aug,
            validation_data=(X_fold_val, y_fold_val),
            epochs=80,
            batch_size=256,
            callbacks=get_advanced_callbacks(),
            class_weight=fold_class_weight_dict,
            verbose=0
        )

        fold_pred = fold_model.predict(X_fold_val, verbose=0).flatten()
        fold_auc = roc_auc_score(y_fold_val, fold_pred)
        fold_scores.append(fold_auc)

    mean_cv_score = np.mean(fold_scores)
    std_cv_score = np.std(fold_scores)

    final_model = create_improved_neural_network(X_all.shape[1])

    X_final_aug, y_final_aug = smart_data_augmentation(X_train, y_train, 0.25)
    final_class_weights = compute_class_weight('balanced', classes=np.unique(y_final_aug), y=y_final_aug)
    final_class_weight_dict = {i: weight for i, weight in enumerate(final_class_weights)}

    final_model.fit(
        X_final_aug, y_final_aug,
        validation_data=(X_val, y_val),
        epochs=100,
        batch_size=256,
        callbacks=get_advanced_callbacks(),
        class_weight=final_class_weight_dict,
        verbose=1
    )

    return final_model, mean_cv_score


if __name__ == "__main__":
    enhanced_features, enhanced_targets = create_enhanced_dataset()

    if len(enhanced_features) == 0:
        exit(1)

    X_all = []
    y_all = []

    for game_features, game_targets in zip(enhanced_features, enhanced_targets):
        for player_features, player_target in zip(game_features, game_targets):
            X_all.append(player_features)
            y_all.append(player_target)

    X_all = np.array(X_all, dtype=np.float32)
    y_all = np.array(y_all, dtype=np.float32)

    scaler = RobustScaler()
    X_all = scaler.fit_transform(X_all)

    X_train, X_temp, y_train, y_temp = train_test_split(
        X_all, y_all, test_size=0.3, random_state=42, stratify=y_all
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp
    )

    X_train_aug, y_train_aug = smart_data_augmentation(X_train, y_train, 0.3)

    rf_model, et_model, gb_model, lr_model = create_sklearn_ensemble()
    nn_model = create_improved_neural_network(X_train.shape[1])

    class_weights = compute_class_weight('balanced', classes=np.unique(y_train_aug), y=y_train_aug)
    class_weight_dict = {i: weight for i, weight in enumerate(class_weights)}

    rf_model.fit(X_train_aug, y_train_aug)

    et_model.fit(X_train_aug, y_train_aug)

    gb_model.fit(X_train_aug, y_train_aug)

    lr_model.fit(X_train_aug, y_train_aug)

    history = nn_model.fit(
        X_train_aug, y_train_aug,
        validation_data=(X_val, y_val),
        epochs=100,
        batch_size=256,
        callbacks=get_advanced_callbacks(),
        class_weight=class_weight_dict,
        verbose=1
    )

    rf_pred = rf_model.predict_proba(X_test)[:, 1]
    et_pred = et_model.predict_proba(X_test)[:, 1]
    gb_pred = gb_model.predict_proba(X_test)[:, 1]
    lr_pred = lr_model.predict_proba(X_test)[:, 1]
    nn_pred = nn_model.predict(X_test, verbose=0).flatten()

    ensemble_pred = (0.3 * rf_pred + 0.2 * et_pred + 0.2 * gb_pred + 0.1 * lr_pred + 0.2 * nn_pred)
    ensemble_pred_binary = (ensemble_pred > 0.5).astype(int)

    ensemble_accuracy = accuracy_score(y_test, ensemble_pred_binary)
    ensemble_f1 = f1_score(y_test, ensemble_pred_binary)
    ensemble_auc = roc_auc_score(y_test, ensemble_pred)

    rf_accuracy = accuracy_score(y_test, (rf_pred > 0.5).astype(int))
    et_accuracy = accuracy_score(y_test, (et_pred > 0.5).astype(int))
    gb_accuracy = accuracy_score(y_test, (gb_pred > 0.5).astype(int))
    lr_accuracy = accuracy_score(y_test, (lr_pred > 0.5).astype(int))
    nn_accuracy = accuracy_score(y_test, (nn_pred > 0.5).astype(int))

    rf_auc = roc_auc_score(y_test, rf_pred)
    et_auc = roc_auc_score(y_test, et_pred)
    gb_auc = roc_auc_score(y_test, gb_pred)
    lr_auc = roc_auc_score(y_test, lr_pred)
    nn_auc = roc_auc_score(y_test, nn_pred)

    models_results = {
        'Random Forest': rf_auc,
        'Extra Trees': et_auc,
        'Gradient Boosting': gb_auc,
        'Logistic Regression': lr_auc,
        'Neural Network': nn_auc,
        'Ensemble': ensemble_auc
    }

    best_model_name = max(models_results, key=models_results.get)
    best_score = models_results[best_model_name]

    improved_model, improved_score = improved_training_loop()

    improved_model.save('neural_network_improved.keras')

    if improved_score > nn_auc:
        best_score = max(best_score, improved_score)
        if improved_score > models_results['Ensemble']:
            best_model_name = 'Improved Neural Network'
    else:
        print("Нужна дополнительная настройка")

    joblib.dump(rf_model, 'sklearn_rf_model.pkl')
    joblib.dump(et_model, 'sklearn_et_model.pkl')
    joblib.dump(gb_model, 'sklearn_gb_model.pkl')
    joblib.dump(lr_model, 'sklearn_lr_model.pkl')
    nn_model.save('sklearn_nn_model.keras')
    joblib.dump(scaler, 'sklearn_scaler.pkl')

    config = {
        'input_dim': int(X_train.shape[1]),
        'ensemble_accuracy': float(ensemble_accuracy),
        'ensemble_auc': float(ensemble_auc),
        'rf_accuracy': float(rf_accuracy),
        'et_accuracy': float(et_accuracy),
        'gb_accuracy': float(gb_accuracy),
        'lr_accuracy': float(lr_accuracy),
        'nn_accuracy': float(nn_accuracy),
        'rf_auc': float(rf_auc),
        'et_auc': float(et_auc),
        'gb_auc': float(gb_auc),
        'lr_auc': float(lr_auc),
        'nn_auc': float(nn_auc),
        'improved_nn_auc': float(improved_score),
        'best_model': best_model_name,
        'best_score': float(best_score),
        'position_lines': POSITION_LINES,
        'tactical_compatibility': TACTICAL_COMPATIBILITY,
        'excluded_positions': EXCLUDED_POSITIONS,
        'feature_names': [
            'height', 'age', 'number', 'primary_position',
            'rating', 'goals_per_game', 'assists_per_game', 'shots_per_game',
            'passes_accuracy', 'duels_won_percent', 'tackles_success',
            'minutes_played_norm', 'start_rate', 'recent_form_rating',
            'recent_goals', 'recent_assists', 'recent_minutes_avg',
            'overall_rating', 'pace_physical',
            'line_0', 'line_1', 'line_2', 'line_3', 'line_4', 'line_5', 'line_6',
            'position_order', 'avg_tactical_compatibility', 'max_tactical_compatibility',
            'opp_avg_strength', 'superiority_factor', 'position_competition',
            'season_start', 'winter_break', 'season_end', 'season_cycle', 'year_cycle', 'calendar_intensity',
            'team_chemistry',
            'derby_factor', 'match_importance', 'personal_motivation',
            'fitness', 'age_factor', 'injury_factor', 'form_factor',
            'base_activity', 'recent_activity', 'injury_status'
        ]
    }

    with open('sklearn_config.json', 'w') as f:
        json.dump(config, f, indent=2)

    if best_model_name == 'Ensemble':
        y_pred_best = ensemble_pred_binary
    elif best_model_name == 'Random Forest':
        y_pred_best = (rf_pred > 0.5).astype(int)
    elif best_model_name == 'Extra Trees':
        y_pred_best = (et_pred > 0.5).astype(int)
    elif best_model_name == 'Gradient Boosting':
        y_pred_best = (gb_pred > 0.5).astype(int)
    elif best_model_name == 'Logistic Regression':
        y_pred_best = (lr_pred > 0.5).astype(int)
    elif best_model_name == 'Improved Neural Network':
        y_pred_best = (improved_model.predict(X_test, verbose=0).flatten() > 0.5).astype(int)
    else:
        y_pred_best = (nn_pred > 0.5).astype(int)


    cm = confusion_matrix(y_test, y_pred_best)
    if rf_auc > 0.6:
        feature_importance = rf_model.feature_importances_
        feature_names = config['feature_names']

        importance_pairs = list(zip(feature_names, feature_importance))
        importance_pairs.sort(key=lambda x: x[1], reverse=True)

        for i, (name, importance) in enumerate(importance_pairs[:15], 1):
            print(f"    {i:2d}. {name}: {importance:.3f}")

    print(f"\n ОБУЧЕНИЕ ЗАВЕРШЕНО УСПЕШНО")