import os
import django
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from keras.models import Model
from keras.layers import Input, Dense, Dropout, BatchNormalization, Concatenate, Reshape
from keras.optimizers import Adam
from keras.callbacks import EarlyStopping, ModelCheckpoint
from keras import regularizers
import json
import pickle

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'football_main.settings')
django.setup()

from game.models import Game, GameStatistic
from player.models import Player, PlayerStatistic, PlayerGameStatistic
from club.models import Club


class ImprovedTeamLineupPredictor:
    def __init__(self):
        self.scaler = StandardScaler()
        self.model = None

        # Структурированные позиции по линиям
        self.position_by_line = {
            0: [11],  # Вратарь
            1: [32, 34, 36, 38, 51, 33, 35, 37, 59],  # Защита
            2: [63, 65, 67, 71, 73, 75, 77, 79, 72, 74, 76, 78],  # Полузащита
            3: [82, 84, 86, 88, 85, 95],  # Атакующая полузащита
            4: [103, 105, 107, 104, 106, 115],  # Нападение
        }

        # Обратный маппинг: позиция -> линия
        self.position_to_line = {}
        for line, positions in self.position_by_line.items():
            for pos in positions:
                self.position_to_line[pos] = line

    def encode_placement_structured(self, placement_data):
        """Структурированное кодирование с учетом линий"""
        if not placement_data:
            return np.zeros(44, dtype=np.float32)  # 11 игроков * 4 (player_id, position_id, line_num, confidence)

        encoded = []

        # Сначала сортируем по линиям для корректной структуры
        structured_players = []

        for line_num, line in enumerate(placement_data):
            for player_pos in line:
                player_id = player_pos.get('id')
                position_id = player_pos.get('position_id')

                if player_id and position_id:
                    try:
                        player_id = float(player_id)
                        position_id = float(position_id)

                        if player_id > 0 and position_id > 0:
                            structured_players.append({
                                'player_id': player_id,
                                'position_id': position_id,
                                'line_num': line_num,
                                'expected_line': self.position_to_line.get(int(position_id), line_num)
                            })
                    except (TypeError, ValueError):
                        continue

        # Сортируем по линиям и позициям
        structured_players.sort(key=lambda x: (x['expected_line'], x['position_id']))

        # Кодируем первых 11 игроков
        for i, player_data in enumerate(structured_players[:11]):
            # Нормализация
            normalized_player_id = (player_data['player_id'] - 3000) / 4000
            normalized_position_id = player_data['position_id'] / 120
            normalized_line = player_data['line_num'] / 4.0

            # Добавляем confidence score (насколько позиция соответствует линии)
            confidence = 1.0 if player_data['line_num'] == player_data['expected_line'] else 0.5

            encoded.extend([
                max(0.0, min(1.0, normalized_player_id)),
                max(0.0, min(1.0, normalized_position_id)),
                max(0.0, min(1.0, normalized_line)),
                confidence
            ])

        # Дополняем до 44 элементов (11 * 4)
        while len(encoded) < 44:
            encoded.append(0.0)

        return np.array(encoded[:44], dtype=np.float32)

    def build_improved_model(self, input_dim, output_dim):
        """Улучшенная архитектура с разделением на блоки"""

        inputs = Input(shape=(input_dim,))

        # Основной блок обработки
        x = Dense(512, activation='relu', kernel_regularizer=regularizers.l2(0.001))(inputs)
        x = BatchNormalization()(x)
        x = Dropout(0.3)(x)

        x = Dense(256, activation='relu', kernel_regularizer=regularizers.l2(0.001))(x)
        x = BatchNormalization()(x)
        x = Dropout(0.3)(x)

        # Разделяем на специализированные блоки

        # Блок для игроков
        player_branch = Dense(128, activation='relu')(x)
        player_branch = Dropout(0.2)(player_branch)
        player_ids = Dense(11, activation='sigmoid', name='player_ids')(player_branch)

        # Блок для позиций
        position_branch = Dense(128, activation='relu')(x)
        position_branch = Dropout(0.2)(position_branch)
        positions = Dense(11, activation='sigmoid', name='positions')(position_branch)

        # Блок для линий
        line_branch = Dense(64, activation='relu')(x)
        line_branch = Dropout(0.2)(line_branch)
        lines = Dense(11, activation='sigmoid', name='lines')(line_branch)

        # Блок для confidence
        conf_branch = Dense(64, activation='relu')(x)
        conf_branch = Dropout(0.1)(conf_branch)
        confidence = Dense(11, activation='sigmoid', name='confidence')(conf_branch)

        # Объединяем выходы
        outputs = Concatenate()([player_ids, positions, lines, confidence])

        model = Model(inputs=inputs, outputs=outputs)

        model.compile(
            optimizer=Adam(learning_rate=0.0005),
            loss='mse',
            metrics=['mae']
        )

        return model

    def add_validation_metrics(self, y_true, y_pred):
        """Добавляет метрики валидации структуры"""
        metrics = {}

        batch_size = len(y_true)

        for i in range(batch_size):
            true_placement = self.decode_prediction(y_true[i])
            pred_placement = self.decode_prediction(y_pred[i])

            # Метрики структуры
            true_lines = len(true_placement)
            pred_lines = len(pred_placement)

            # Процент правильных позиций
            correct_positions = 0
            total_positions = 0

            for line_idx in range(min(true_lines, pred_lines)):
                true_line = true_placement[line_idx] if line_idx < true_lines else []
                pred_line = pred_placement[line_idx] if line_idx < pred_lines else []

                for player in true_line:
                    total_positions += 1
                    true_pos = player.get('position_id')

                    # Ищем соответствующую позицию в предсказании
                    for pred_player in pred_line:
                        pred_pos = pred_player.get('position_id')
                        if abs(true_pos - pred_pos) < 5:  # Допускаем небольшую погрешность
                            correct_positions += 1
                            break

            if total_positions > 0:
                position_accuracy = correct_positions / total_positions
            else:
                position_accuracy = 0.0

            metrics[f'sample_{i}_position_accuracy'] = position_accuracy

        return metrics

    def prepare_training_data(self):
        """Подготавливает данные с улучшенной валидацией"""
        print("Загрузка данных для обучения...")

        games = Game.objects.filter(
            is_finished=True,
            game_date__year__gte=2015,  # Берем более свежие данные
            home_club_placement__isnull=False,
            away_club_placement__isnull=False,
            home_players__isnull=False,
            away_players__isnull=False
        ).order_by('game_date')

        valid_games = []

        for game in games:
            # Более строгая валидация
            if (self.is_valid_placement(game.home_club_placement) and
                    self.is_valid_placement(game.away_club_placement) and
                    self.is_valid_players_list(game.home_players) and
                    self.is_valid_players_list(game.away_players) and
                    self.has_goalkeeper(game.home_club_placement) and
                    self.has_goalkeeper(game.away_club_placement)):
                valid_games.append(game)

        print(f"Валидных игр: {len(valid_games)}")

        X_data = []
        y_data = []

        for game in valid_games:
            # Домашняя команда
            home_features = self.create_game_features(game, predict_home=True)
            if home_features is not None:
                home_encoded = self.encode_placement_structured(game.home_club_placement)
                if len(home_encoded) == 44:
                    X_data.append(home_features)
                    y_data.append(home_encoded)

            # Гостевая команда
            away_features = self.create_game_features(game, predict_home=False)
            if away_features is not None:
                away_encoded = self.encode_placement_structured(game.away_club_placement)
                if len(away_encoded) == 44:
                    X_data.append(away_features)
                    y_data.append(away_encoded)

        print(f"Всего примеров: {len(X_data)}")
        return np.array(X_data), np.array(y_data)

    def has_goalkeeper(self, placement_data):
        """Проверяет наличие вратаря в составе"""
        for line in placement_data:
            for player in line:
                if player.get('position_id') == 11:
                    return True
        return False

    def is_valid_placement(self, placement_data):
        """Улучшенная валидация расстановки"""
        if not placement_data or not isinstance(placement_data, list):
            return False

        total_players = 0
        has_gk = False

        for line in placement_data:
            if not isinstance(line, list):
                return False

            for player_pos in line:
                if not isinstance(player_pos, dict):
                    return False

                player_id = player_pos.get('id')
                position_id = player_pos.get('position_id')

                if player_id is None or player_id == 0:
                    return False
                if position_id is None or position_id == 0:
                    return False

                if position_id == 11:
                    has_gk = True

                try:
                    float(player_id)
                    float(position_id)
                except (TypeError, ValueError):
                    return False

                total_players += 1

        return total_players == 11 and has_gk

    def is_valid_players_list(self, players_list):
        """Улучшенная валидация списка игроков"""
        if not players_list or not isinstance(players_list, list):
            return False

        valid_players = 0
        for player_id in players_list:
            if player_id is not None and player_id != 0:
                try:
                    float(player_id)
                    valid_players += 1
                except (TypeError, ValueError):
                    continue

        return valid_players >= 11

    # Остальные методы остаются такими же, как в оригинальном коде
    # но с обновленными размерностями данных (44 вместо 33)

    def decode_prediction(self, prediction):
        """Декодирует предсказание в структуру расстановки"""
        if len(prediction) != 44:
            return []

        placement = [[], [], [], [], []]  # 5 линий

        # Разбираем предсказание по группам
        for i in range(11):
            start_idx = i * 4
            if start_idx + 3 < len(prediction):
                # Денормализуем
                player_id = (prediction[start_idx] * 4000) + 3000
                position_id = int(prediction[start_idx + 1] * 120)
                line_num = int(prediction[start_idx + 2] * 4)
                confidence = prediction[start_idx + 3]

                # Корректируем позицию и линию
                position_id = self.correct_position_id(position_id)
                expected_line = self.position_to_line.get(position_id, line_num)

                # Используем expected_line если confidence низкий
                final_line = expected_line if confidence < 0.7 else line_num
                final_line = max(0, min(4, final_line))

                placement[final_line].append({
                    'id': int(player_id),
                    'position_id': position_id
                })

        return [line for line in placement if line]  # Убираем пустые линии

    def correct_position_id(self, position_id):
        """Корректирует position_id к валидным значениям"""
        valid_positions = [
            11, 32, 34, 36, 38, 51, 33, 35, 37, 59,
            63, 65, 67, 71, 73, 75, 77, 79, 72, 74, 76, 78,
            82, 84, 86, 88, 85, 95,
            103, 105, 107, 104, 106, 115,
        ]

        if position_id in valid_positions:
            return position_id

        return min(valid_positions, key=lambda x: abs(x - position_id))