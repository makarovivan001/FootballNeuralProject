import os
import django
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from keras.src.saving import load_model
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from keras.models import Model
from keras.layers import Input, Dense, Dropout, BatchNormalization, Concatenate
from keras.optimizers import Adam
from keras.callbacks import EarlyStopping, ModelCheckpoint
import json
import pickle

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'football_main.settings')
django.setup()

from game.models import Game, GameStatistic
from player.models import Player, PlayerStatistic, PlayerGameStatistic
from club.models import Club


class TeamLineupPredictor:
    def __init__(self):
        self.scaler = StandardScaler()
        self.position_encoder = LabelEncoder()
        self.model = None
        self.position_mappings = {
            11: 'GK',
            32: 'LB', 34: 'CB', 36: 'CB', 38: 'RB',
            51: 'LWB', 33: 'CB', 35: 'CB', 37: 'CB', 59: 'RWB',

            63: 'CM', 65: 'CDM', 67: 'CM',

            71: 'LM', 73: 'CM', 75: 'CM', 77: 'CM', 79: 'RM',
            72: 'LM', 74: 'CM', 76: 'CM', 78: 'RM',

            82: 'LW', 84: 'CM', 86: 'CM', 88: 'RW',
            85: 'CM',
            95: 'CAM',

            103: 'LW', 105: 'ST', 107: 'RW',
            104: 'ST', 106: 'ST',
            115: 'ST',
        }

    def is_valid_placement(self, placement_data):
        """Более гибкая проверка валидности данных расстановки"""
        if not placement_data or not isinstance(placement_data, list):
            return False

        total_players = 0
        for line in placement_data:
            if not isinstance(line, list):
                continue  # Пропускаем невалидные линии вместо отклонения всего

            for player_pos in line:
                if not isinstance(player_pos, dict):
                    continue  # Пропускаем невалидные позиции

                player_id = player_pos.get('id')
                position_id = player_pos.get('position_id')

                # Более мягкая проверка - любые положительные числа
                try:
                    if player_id and position_id and float(player_id) > 0 and float(position_id) > 0:
                        total_players += 1
                except (TypeError, ValueError):
                    continue  # Пропускаем невалидные данные

        # Принимаем составы от 8 до 15 игроков (реальные данные могут варьироваться)
        return 8 <= total_players <= 15

    def is_valid_players_list(self, players_list):
        """Более гибкая проверка списка игроков"""
        if not players_list or not isinstance(players_list, list):
            return False

        valid_count = 0
        for player_id in players_list:
            try:
                if player_id and float(player_id) > 0:
                    valid_count += 1
            except (TypeError, ValueError):
                continue

        # Принимаем списки с минимум 8 валидными игроками
        return valid_count >= 8

    def extract_formation_features(self, placement_data):
        """РАСШИРЕННОЕ извлечение признаков формации с анализом структуры - СОХРАНЯЕМ ОРИГИНАЛ"""
        if not placement_data:
            return np.zeros(25)  # Сохраняем оригинальный размер

        features = []

        # 1. Базовые признаки
        formation_lines = len(placement_data)
        features.append(float(formation_lines))  # Количество линий

        # 2. Детальный анализ линий (до 6 возможных линий)
        line_counts = []
        line_avg_positions = []

        for i in range(6):  # Анализируем до 6 линий
            if i < len(placement_data):
                line = placement_data[i]
                valid_players_in_line = 0
                position_sum = 0

                if isinstance(line, list):
                    for p in line:
                        if isinstance(p, dict):
                            try:
                                player_id = p.get('id', 0)
                                position_id = p.get('position_id', 0)
                                if player_id and position_id and float(player_id) > 0 and float(position_id) > 0:
                                    valid_players_in_line += 1
                                    position_sum += float(position_id)
                            except (TypeError, ValueError):
                                continue

                line_counts.append(float(valid_players_in_line))

                # Средняя позиция в линии
                if valid_players_in_line > 0:
                    avg_pos = position_sum / valid_players_in_line
                    line_avg_positions.append(float(avg_pos))
                else:
                    line_avg_positions.append(0.0)
            else:
                line_counts.append(0.0)
                line_avg_positions.append(0.0)

        features.extend(line_counts)  # +6 признаков
        features.extend(line_avg_positions)  # +6 признаков

        # 3. Тактический анализ формации
        total_players = sum(line_counts)
        if total_players > 0:
            # Распределение игроков по линиям (%)
            line_ratios = [count / total_players for count in line_counts]
            features.extend(line_ratios)  # +6 признаков

            # 4. Тип формации (классификация) - СОХРАНЯЕМ
            formation_type = self.classify_formation_type(line_counts[:formation_lines])
            features.append(float(formation_type))  # +1 признак

            # 5. Компактность формации
            non_zero_lines = [c for c in line_counts if c > 0]
            if len(non_zero_lines) > 1:
                formation_variance = float(np.var(non_zero_lines))
                formation_balance = float(np.std(non_zero_lines))
            else:
                formation_variance = 0.0
                formation_balance = 0.0

            features.extend([formation_variance, formation_balance])  # +2 признака
        else:
            features.extend([0.0] * 9)  # Заполняем нулями если нет игроков

        # Убеждаемся что у нас ровно 25 признаков
        while len(features) < 25:
            features.append(0.0)

        return np.array(features[:25], dtype=np.float32)

    def classify_formation_type(self, line_counts):
        """Классифицирует тип формации - СОХРАНЯЕМ ОРИГИНАЛ"""
        if not line_counts or len(line_counts) < 2:
            return 0  # Неизвестно

        # Убираем вратаря (первая линия обычно = 1)
        field_lines = line_counts[1:] if line_counts[0] == 1 else line_counts

        if len(field_lines) == 3:  # 3 линии
            if field_lines == [4, 4, 2]:
                return 1  # 4-4-2
            elif field_lines == [4, 3, 3]:
                return 2  # 4-3-3
            elif field_lines == [3, 5, 2]:
                return 3  # 3-5-2
            elif field_lines == [5, 3, 2]:
                return 4  # 5-3-2
            else:
                return 5  # Другая 3-линейная

        elif len(field_lines) == 4:  # 4 линии
            if field_lines == [4, 2, 3, 1]:
                return 6  # 4-2-3-1
            elif field_lines == [4, 3, 1, 2]:
                return 7  # 4-3-1-2
            elif field_lines == [3, 4, 2, 1]:
                return 8  # 3-4-2-1
            else:
                return 9  # Другая 4-линейная

        elif len(field_lines) == 5:  # 5 линий
            return 10  # 5-линейная формация

        return 0  # Неклассифицированная

    def get_team_formation_history(self, club_id, target_date, games_count=10):
        """Получает историю формаций команды за последние игры - СОХРАНЯЕМ ОРИГИНАЛ"""
        try:
            recent_games = Game.objects.filter(
                models.Q(home_club_id=club_id) | models.Q(away_club_id=club_id),
                game_date__lt=target_date,
                is_finished=True
            ).order_by('-game_date')[:games_count]

            formation_features = []

            for game in recent_games:
                try:
                    if game.home_club_id == club_id and game.home_club_placement:
                        placement = game.home_club_placement
                    elif game.away_club_id == club_id and game.away_club_placement:
                        placement = game.away_club_placement
                    else:
                        continue  # Пропускаем игру без данных

                    # Анализируем формацию
                    formation_analysis = self.analyze_formation_structure(placement)
                    if formation_analysis and len(formation_analysis) == 5:
                        formation_features.append(formation_analysis)
                except Exception:
                    continue  # Пропускаем проблемные игры

            # Если нет данных, возвращаем нули
            if not formation_features:
                return np.zeros(15)

            # Агрегируем статистику по формациям
            formations_array = np.array(formation_features)

            aggregated_features = []

            # Средние значения
            mean_features = np.mean(formations_array, axis=0)
            aggregated_features.extend(mean_features.tolist())  # +5

            # Стандартные отклонения (стабильность тактики)
            std_features = np.std(formations_array, axis=0)
            aggregated_features.extend(std_features.tolist())  # +5

            # Наиболее частая формация
            line_counts = [f[0] for f in formation_features]  # Количество линий
            most_common_lines = max(set(line_counts), key=line_counts.count) if line_counts else 3
            aggregated_features.append(float(most_common_lines))  # +1

            # Тактическая гибкость (количество разных формаций)
            unique_formations = len(set(tuple(f) for f in formation_features))
            aggregated_features.append(float(unique_formations))  # +1

            # Тенденция к атаке/защите
            attack_tendency = np.mean([f[3] for f in formation_features])  # Игроки в атаке
            defense_tendency = np.mean([f[1] for f in formation_features])  # Игроки в защите
            aggregated_features.extend([attack_tendency, defense_tendency])  # +2

            # Стабильность количества линий
            line_stability = 1.0 - (np.std(line_counts) / (np.mean(line_counts) + 0.001))
            aggregated_features.append(float(line_stability))  # +1

            # Гарантируем размер 15
            while len(aggregated_features) < 15:
                aggregated_features.append(0.0)

            return np.array(aggregated_features[:15])
        except Exception as e:
            print(f"Ошибка в get_team_formation_history: {e}")
            return np.zeros(15)

    def analyze_formation_structure(self, placement_data):
        """Анализирует структуру конкретной формации - СОХРАНЯЕМ ОРИГИНАЛ"""
        if not placement_data:
            return [3, 4, 3, 2, 0.5]  # Значения по умолчанию

        line_counts = []
        for line in placement_data:
            if isinstance(line, list):
                valid_count = 0
                for player_pos in line:
                    if isinstance(player_pos, dict):
                        try:
                            player_id = player_pos.get('id', 0)
                            position_id = player_pos.get('position_id', 0)
                            if player_id and position_id and float(player_id) > 0 and float(position_id) > 0:
                                valid_count += 1
                        except (TypeError, ValueError):
                            continue
                line_counts.append(valid_count)
            else:
                line_counts.append(0)

        features = [
            len(line_counts),  # Количество линий
            line_counts[1] if len(line_counts) > 1 else 0,  # Защитники
            line_counts[2] if len(line_counts) > 2 else 0,  # Полузащитники
            line_counts[-1] if len(line_counts) > 0 else 0,  # Нападающие
            len(line_counts) / 5.0  # Нормализованная сложность
        ]

        return features

    def build_adaptive_model(self, input_dim, output_dim):
        """Архитектура с предсказанием структуры формации - СОХРАНЯЕМ ОРИГИНАЛ"""

        inputs = Input(shape=(input_dim,))

        # Общий энкодер
        x = Dense(512, activation='relu')(inputs)
        x = BatchNormalization()(x)
        x = Dropout(0.3)(x)

        x = Dense(256, activation='relu')(x)
        x = BatchNormalization()(x)
        x = Dropout(0.3)(x)

        shared_repr = Dense(128, activation='relu')(x)
        shared_repr = Dropout(0.2)(shared_repr)

        # Ветка предсказания структуры формации
        formation_branch = Dense(64, activation='relu', name='formation_branch')(shared_repr)
        formation_branch = Dropout(0.2)(formation_branch)

        # Предсказание количества линий (2-6)
        num_lines = Dense(5, activation='softmax', name='num_lines')(formation_branch)

        # Предсказание распределения игроков по линиям
        line_distribution = Dense(6, activation='softmax', name='line_distribution')(formation_branch)

        # Ветка предсказания игроков
        players_branch = Dense(128, activation='relu', name='players_branch')(shared_repr)
        players_branch = Dropout(0.2)(players_branch)

        players_branch = Dense(64, activation='relu')(players_branch)
        players_branch = Dropout(0.2)(players_branch)

        # Предсказание игроков (33 элемента)
        player_predictions = Dense(33, activation='sigmoid', name='player_predictions')(players_branch)

        # Объединяем все выходы
        all_outputs = Concatenate()([num_lines, line_distribution, player_predictions])

        model = Model(inputs=inputs, outputs=all_outputs)

        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )

        return model

    def create_game_features_enhanced(self, game, predict_home=True):
        """Расширенное создание признаков с историей формаций - ИСПРАВЛЯЕМ ТОЛЬКО ПРОВЕРКИ"""
        try:
            if predict_home:
                target_club_id = game.home_club_id
                opponent_club_id = game.away_club_id
                opponent_placement = game.away_club_placement
                opponent_players = game.away_players or []
            else:
                target_club_id = game.away_club_id
                opponent_club_id = game.home_club_id
                opponent_placement = game.home_club_placement
                opponent_players = game.home_players or []

            if not opponent_placement or not opponent_players:
                return None

            # Базовые признаки команд - УБИРАЕМ ЖЕСТКИЕ ПРОВЕРКИ
            target_team_features = self.get_team_stats_features(target_club_id, game.game_date)
            # Нормализуем размер до 80
            if len(target_team_features) != 80:
                if len(target_team_features) > 80:
                    target_team_features = target_team_features[:80]
                else:
                    target_team_features = np.pad(target_team_features, (0, 80 - len(target_team_features)), 'constant')

            opponent_team_features = self.get_team_stats_features(opponent_club_id, game.game_date)
            # Нормализуем размер до 80
            if len(opponent_team_features) != 80:
                if len(opponent_team_features) > 80:
                    opponent_team_features = opponent_team_features[:80]
                else:
                    opponent_team_features = np.pad(opponent_team_features, (0, 80 - len(opponent_team_features)),
                                                    'constant')

            # РАСШИРЕННЫЕ признаки формаций
            opponent_formation_features = self.extract_formation_features(opponent_placement)  # 25

            # История формаций целевой команды
            target_formation_history = self.get_team_formation_history(target_club_id, game.game_date)  # 15

            # История формаций соперника
            opponent_formation_history = self.get_team_formation_history(opponent_club_id, game.game_date)  # 15

            # Признаки игроков - УБИРАЕМ ЖЕСТКИЕ ПРОВЕРКИ
            opponent_player_features = self.get_player_stats_features(opponent_players, game.game_date)  # 330
            # Нормализуем размер до 330
            if len(opponent_player_features) != 330:
                if len(opponent_player_features) > 330:
                    opponent_player_features = opponent_player_features[:330]
                else:
                    opponent_player_features = np.pad(opponent_player_features,
                                                      (0, 330 - len(opponent_player_features)), 'constant')

            # Дополнительные признаки
            additional_features = np.array([
                1.0 if predict_home else 0.0,
                float(game.game_date.weekday()),
                float(getattr(game, 'tour', 0)),
            ])  # 3

            # Объединяем все признаки
            all_features = np.concatenate([
                target_team_features,  # 80
                opponent_team_features,  # 80
                opponent_formation_features,  # 25
                target_formation_history,  # 15
                opponent_formation_history,  # 15
                opponent_player_features,  # 330
                additional_features  # 3
            ])  # Итого: 548

            # Обрезаем до 500 для стабильности
            final_features = all_features[:500]
            return final_features

        except Exception as e:
            print(f"Ошибка создания расширенных признаков в игре {game.id}: {e}")
            return None

    def encode_placement_adaptive(self, placement_data):
        """Адаптивное кодирование с предсказанием структуры - СОХРАНЯЕМ ОРИГИНАЛ"""
        if not placement_data:
            return np.zeros(44, dtype=np.float32)  # 5 + 6 + 33

        # Анализ структуры
        line_counts = []
        for line in placement_data:
            if isinstance(line, list):
                valid_count = 0
                for player_pos in line:
                    if isinstance(player_pos, dict):
                        try:
                            player_id = player_pos.get('id', 0)
                            position_id = player_pos.get('position_id', 0)
                            if player_id and position_id and float(player_id) > 0 and float(position_id) > 0:
                                valid_count += 1
                        except (TypeError, ValueError):
                            continue
                line_counts.append(valid_count)
            else:
                line_counts.append(0)

        num_lines = len(line_counts)

        # Кодируем количество линий (one-hot для 2-6 линий)
        lines_encoded = np.zeros(5)
        if 2 <= num_lines <= 6:
            lines_encoded[num_lines - 2] = 1.0

        # Кодируем распределение игроков по линиям
        distribution = np.zeros(6)
        total_players = sum(line_counts)
        for i, count in enumerate(line_counts[:6]):
            distribution[i] = count / max(total_players, 1)  # Избегаем деления на ноль

        # Стандартное кодирование игроков
        players_encoded = np.zeros(33)
        encoded_idx = 0

        for line_num, line in enumerate(placement_data):
            if not isinstance(line, list):
                continue
            for player_pos in line:
                if encoded_idx >= 33:
                    break
                if not isinstance(player_pos, dict):
                    continue

                try:
                    player_id = player_pos.get('id', 0)
                    position_id = player_pos.get('position_id', 0)

                    if player_id and position_id:
                        player_id = float(player_id)
                        position_id = float(position_id)

                        if player_id > 0 and position_id > 0:
                            # Нормализация
                            norm_player_id = (player_id - 3000) / 4000
                            norm_position_id = position_id / 120
                            norm_line_num = line_num / 5.0

                            if encoded_idx + 2 < 33:
                                players_encoded[encoded_idx:encoded_idx + 3] = [
                                    max(0.0, min(1.0, norm_player_id)),
                                    max(0.0, min(1.0, norm_position_id)),
                                    norm_line_num
                                ]
                                encoded_idx += 3
                except (TypeError, ValueError):
                    continue

        # Объединяем все части
        full_encoding = np.concatenate([lines_encoded, distribution, players_encoded])
        return full_encoding[:44]

    def get_player_stats_features(self, player_ids, target_date):
        """Получает статистические признаки игроков - СОХРАНЯЕМ ПОЛНУЮ ФУНКЦИОНАЛЬНОСТЬ"""
        features = []

        # Обрабатываем только первых 11 игроков
        valid_player_ids = []
        for pid in (player_ids or []):
            try:
                if pid and float(pid) > 0:
                    valid_player_ids.append(int(float(pid)))
            except (TypeError, ValueError):
                continue

        valid_player_ids = valid_player_ids[:11]

        for i in range(11):  # Всегда 11 игроков
            if i < len(valid_player_ids):
                player_id = valid_player_ids[i]
                try:
                    player = Player.objects.get(identifier=player_id)

                    # Основная статистика игрока
                    if hasattr(player, 'statistic') and player.statistic:
                        stats = player.statistic
                        player_features = [
                            float(stats.rating if stats.rating else 0),
                            float(stats.goals if stats.goals else 0),
                            float(stats.assists if stats.assists else 0),
                            float(stats.shots if stats.shots else 0),
                            float(stats.successful_passes_accuracy if stats.successful_passes_accuracy else 0),
                            float(stats.minutes_played if stats.minutes_played else 0),
                            float(stats.started if stats.started else 0),
                            float(stats.yellow_cards if stats.yellow_cards else 0),
                            float(stats.red_cards if stats.red_cards else 0),
                            float(stats.tackles_succeeded_percent if stats.tackles_succeeded_percent else 0),
                        ]
                    else:
                        player_features = [0.0] * 10

                    # Статистика за последние игры - СОХРАНЯЕМ ОРИГИНАЛ
                    try:
                        recent_games = PlayerGameStatistic.objects.filter(
                            player=player,
                            game__game_date__lt=target_date
                        ).order_by('-game__game_date')[:5]

                        recent_stats = []
                        for game_stat in recent_games:
                            recent_stats.extend([
                                float(game_stat.rating_title if game_stat.rating_title else 0),
                                float(game_stat.minutes_played if game_stat.minutes_played else 0),
                                float(game_stat.goals if game_stat.goals else 0),
                                float(game_stat.assists if game_stat.assists else 0)
                            ])

                        # Дополняем до 20 признаков (5 игр * 4 показателя)
                        while len(recent_stats) < 20:
                            recent_stats.append(0.0)

                        player_features.extend(recent_stats[:20])
                    except Exception:
                        player_features.extend([0.0] * 20)

                except Player.DoesNotExist:
                    player_features = [0.0] * 30
                except Exception:
                    player_features = [0.0] * 30
            else:
                # Если игроков меньше 11, дополняем нулями
                player_features = [0.0] * 30

            features.extend(player_features)

        # Гарантируем размер 330 (11 игроков * 30 признаков)
        if len(features) != 330:
            if len(features) > 330:
                features = features[:330]
            else:
                features.extend([0.0] * (330 - len(features)))

        return np.array(features)

    def get_team_stats_features(self, club_id, target_date):
        """Получает статистические признаки команды - СОХРАНЯЕМ ОРИГИНАЛ"""
        try:
            # Последние 10 игр команды
            recent_games = Game.objects.filter(
                models.Q(home_club_id=club_id) | models.Q(away_club_id=club_id),
                game_date__lt=target_date,
                is_finished=True
            ).order_by('-game_date')[:10]

            features = []

            for game in recent_games:
                try:
                    is_home = game.home_club_id == club_id

                    # Результат игры
                    if is_home:
                        goals_for = game.home_score or 0
                        goals_against = game.away_score or 0
                    else:
                        goals_for = game.away_score or 0
                        goals_against = game.home_score or 0

                    features.extend([float(goals_for), float(goals_against)])

                    # Статистика команды в игре
                    try:
                        team_stats = GameStatistic.objects.get(
                            game=game,
                            club_id=club_id
                        )

                        game_features = [
                            float(team_stats.total_shots or 0),
                            float(team_stats.shots_on_target or 0),
                            float(team_stats.accurate_passes_persent or 0),
                            float(team_stats.corners or 0),
                            float(team_stats.yellow_cards or 0),
                            float(team_stats.red_cards or 0)
                        ]
                    except GameStatistic.DoesNotExist:
                        game_features = [0.0] * 6

                    features.extend(game_features)
                except Exception:
                    features.extend([0.0] * 8)  # 2 + 6

            # Дополняем до 10 игр если данных меньше
            while len(features) < 10 * 8:  # 10 игр * 8 признаков
                features.extend([0.0] * 8)

            # Гарантируем размер 80
            if len(features) != 80:
                if len(features) > 80:
                    features = features[:80]
                else:
                    features.extend([0.0] * (80 - len(features)))

            return np.array(features)
        except Exception as e:
            print(f"Ошибка в get_team_stats_features: {e}")
            return np.zeros(80)

    def prepare_training_data(self):
        """Подготавливает данные для обучения - ИСПРАВЛЯЕМ ТОЛЬКО ВАЛИДАЦИЮ"""
        print("Загрузка данных для обучения...")

        # Получаем все завершенные игры с 2010 года
        games = Game.objects.filter(
            is_finished=True,
            game_date__year__gte=2010,
            home_club_placement__isnull=False,
            away_club_placement__isnull=False,
            home_players__isnull=False,
            away_players__isnull=False
        ).order_by('game_date')

        print(f"Найдено игр в базе: {games.count()}")

        # Фильтруем игры с валидными данными - БОЛЕЕ МЯГКАЯ ВАЛИДАЦИЯ
        valid_games = []
        invalid_reasons = {
            'invalid_home_placement': 0,
            'invalid_away_placement': 0,
            'invalid_home_players': 0,
            'invalid_away_players': 0
        }

        for game in games:
            is_valid = True

            # Проверяем домашнюю расстановку
            if not self.is_valid_placement(game.home_club_placement):
                invalid_reasons['invalid_home_placement'] += 1
                is_valid = False

            # Проверяем гостевую расстановку
            if not self.is_valid_placement(game.away_club_placement):
                invalid_reasons['invalid_away_placement'] += 1
                is_valid = False

            # Проверяем домашних игроков
            if not self.is_valid_players_list(game.home_players):
                invalid_reasons['invalid_home_players'] += 1
                is_valid = False

            # Проверяем гостевых игроков
            if not self.is_valid_players_list(game.away_players):
                invalid_reasons['invalid_away_players'] += 1
                is_valid = False

            if is_valid:
                valid_games.append(game)

        print(f"Валидных игр: {len(valid_games)} из {games.count()}")
        print("Причины отклонения игр:")
        for reason, count in invalid_reasons.items():
            if count > 0:
                print(f"  {reason}: {count}")

        # ДИАГНОСТИКА: Проверяем первые несколько валидных игр
        sample_games = valid_games[-20:] if len(valid_games) >= 20 else valid_games
        for i, game in enumerate(sample_games):
            print(f"\nОбразец валидной игры {i + 1} (ID: {game.id}):")
            print(f"  home_club_placement: {len(game.home_club_placement)} линий")
            print(f"  away_club_placement: {len(game.away_club_placement)} линий")
            print(f"  home_players: {len(game.home_players)} игроков")
            print(f"  away_players: {len(game.away_players)} игроков")

            # Тестируем функцию extract_formation_features
            home_features = self.extract_formation_features(game.home_club_placement)
            away_features = self.extract_formation_features(game.away_club_placement)
            print(f"  home formation features: {len(home_features)} элементов")
            print(f"  away formation features: {len(away_features)} элементов")

        X_data = []
        y_data = []
        processed_games = 0

        failed_reasons = {
            'create_features_failed': 0,
            'encoding_failed': 0,
            'size_mismatch': 0,
            'exception': 0
        }

        for game in valid_games:
            processed_games += 1

            if processed_games % 100 == 0:
                print(f"Обработано игр: {processed_games}, создано примеров: {len(X_data)}")

            # Создаем два примера для каждой игры (домашняя и гостевая команды)

            # 1. Предсказываем состав домашней команды на основе гостевой
            try:
                home_features = self.create_game_features_enhanced(game, predict_home=True)
                if home_features is not None and len(home_features) == 500:
                    home_encoded = self.encode_placement_adaptive(game.home_club_placement)
                    if len(home_encoded) == 44:
                        X_data.append(home_features)
                        y_data.append(home_encoded)
                    else:
                        failed_reasons['encoding_failed'] += 1
                else:
                    failed_reasons['create_features_failed'] += 1
            except Exception as e:
                failed_reasons['exception'] += 1
                if processed_games % 500 == 0:
                    print(f"Ошибка в домашней команде игры {game.id}: {e}")

            # 2. Предсказываем состав гостевой команды на основе домашней
            try:
                away_features = self.create_game_features_enhanced(game, predict_home=False)
                if away_features is not None and len(away_features) == 500:
                    away_encoded = self.encode_placement_adaptive(game.away_club_placement)
                    if len(away_encoded) == 44:
                        X_data.append(away_features)
                        y_data.append(away_encoded)
                    else:
                        failed_reasons['encoding_failed'] += 1
                else:
                    failed_reasons['create_features_failed'] += 1
            except Exception as e:
                failed_reasons['exception'] += 1
                if processed_games % 500 == 0:
                    print(f"Ошибка в гостевой команде игры {game.id}: {e}")

        print(f"Обработано игр: {processed_games}")
        print(f"Всего примеров для обучения: {len(X_data)}")
        print(f"Размер входных признаков: {len(X_data[0]) if X_data else 0}")
        print(f"Размер выходных данных: {len(y_data[0]) if y_data else 0}")

        print(f"\nСтатистика отклонений при обработке:")
        for reason, count in failed_reasons.items():
            if count > 0:
                print(f"  {reason}: {count}")

        if not X_data:
            raise ValueError("Нет валидных данных для обучения!")

        # Проверяем консистентность размеров
        feature_sizes = [len(x) for x in X_data]
        target_sizes = [len(y) for y in y_data]

        if len(set(feature_sizes)) > 1:
            print(f"ПРЕДУПРЕЖДЕНИЕ: Разные размеры признаков: {set(feature_sizes)}")
            # Нормализуем все к одному размеру
            max_size = max(feature_sizes)
            normalized_X = []
            for x in X_data:
                if len(x) < max_size:
                    x_normalized = np.pad(x, (0, max_size - len(x)), 'constant')
                else:
                    x_normalized = x[:max_size]
                normalized_X.append(x_normalized)
            X_data = normalized_X

        if len(set(target_sizes)) > 1:
            print(f"ПРЕДУПРЕЖДЕНИЕ: Разные размеры целевых переменных: {set(target_sizes)}")
            # Нормализуем все к одному размеру
            max_size = max(target_sizes)
            normalized_y = []
            for y in y_data:
                if len(y) < max_size:
                    y_normalized = np.pad(y, (0, max_size - len(y)), 'constant')
                else:
                    y_normalized = y[:max_size]
                normalized_y.append(y_normalized)
            y_data = normalized_y

        return np.array(X_data), np.array(y_data)

    def build_model(self, input_dim, output_dim):
        """Используем адаптивную модель - СОХРАНЯЕМ ОРИГИНАЛ"""
        return self.build_adaptive_model(input_dim, output_dim)

    def get_available_players(self, club_id, target_date):
        """Получает список доступных игроков команды"""
        try:
            recent_games = Game.objects.filter(
                models.Q(home_club_id=club_id) | models.Q(away_club_id=club_id),
                game_date__lt=target_date,
                is_finished=True
            ).order_by('-game_date')[:5]

            player_ids = set()

            for game in recent_games:
                try:
                    if game.home_club_id == club_id and game.home_players:
                        player_ids.update([pid for pid in game.home_players if pid])
                    elif game.away_players:
                        player_ids.update([pid for pid in game.away_players if pid])
                except Exception:
                    continue

            return list(player_ids)
        except Exception:
            return list(range(4000, 4020))  # Fallback

    def get_position_for_line(self, line_idx, suggested_position_id=None):
        """Возвращает подходящую позицию для линии"""
        line_positions = {
            0: 11,  # GK
            1: 34,  # CB для защиты
            2: 76,  # CM для полузащиты
            3: 95,  # CAM для атакующей полузащиты
            4: 105  # ST для нападения
        }

        default_pos = line_positions.get(line_idx, 76)

        # Если есть предложенная позиция, проверяем подходит ли она для линии
        if suggested_position_id:
            position_line_map = {
                11: 0,  # GK
                32: 1, 34: 1, 36: 1, 38: 1, 51: 1, 33: 1, 35: 1, 37: 1, 59: 1,  # DEF
                63: 2, 65: 2, 67: 2, 71: 2, 73: 2, 75: 2, 77: 2, 79: 2, 72: 2, 74: 2, 76: 2, 78: 2,  # MID
                95: 3, 82: 3, 84: 3, 86: 3, 88: 3, 85: 3,  # CAM
                103: 4, 105: 4, 107: 4, 104: 4, 106: 4, 115: 4,  # ATT
            }

            suggested_line = position_line_map.get(suggested_position_id)
            if suggested_line == line_idx:
                return suggested_position_id

        return default_pos

    def find_goalkeeper(self, available_players, player_positions):
        """Находит вратаря среди доступных игроков"""
        for player_id in available_players:
            player_pos = player_positions.get(player_id, '').lower()
            if 'goalkeeper' in player_pos or 'gk' in player_pos:
                return player_id

        # Если нет явного вратаря, возвращаем None
        return None

    def find_closest_available_player(self, target_id, available_players, used_players, player_positions):
        """Находит ближайшего доступного игрока"""
        best_player = None
        min_diff = float('inf')

        for player_id in available_players:
            if player_id not in used_players:
                try:
                    diff = abs(float(player_id) - float(target_id))
                    if diff < min_diff:
                        min_diff = diff
                        best_player = player_id
                except (TypeError, ValueError):
                    continue

        return best_player

    def correct_position_id(self, position_id):
        """Корректирует position_id к валидному значению"""
        valid_positions = list(self.position_mappings.keys())

        try:
            pos = int(position_id)
            if pos in valid_positions:
                return pos

            # Находим ближайшую валидную позицию
            closest = min(valid_positions, key=lambda x: abs(x - pos))
            return closest
        except (TypeError, ValueError):
            return 34  # Default CB

    def smart_decode_placement_adaptive(self, prediction, club_id, target_date):
        """Адаптивное декодирование с использованием предсказанной структуры - СОХРАНЯЕМ ОРИГИНАЛ"""

        if len(prediction) < 44:
            # Fallback к простому методу
            return self.decode_placement_simple(prediction, club_id, target_date)

        # Извлекаем компоненты предсказания
        lines_prediction = prediction[:5]  # Количество линий
        distribution = prediction[5:11]  # Распределение игроков
        players_data = prediction[11:44]  # Данные игроков

        # Определяем предсказанное количество линий
        predicted_lines = np.argmax(lines_prediction) + 2  # 2-6 линий

        print(f"Предсказано линий: {predicted_lines}")
        print(f"Распределение: {[f'{d:.2f}' for d in distribution]}")

        # Получаем доступных игроков
        available_players = self.get_available_players(club_id, target_date)
        if not available_players:
            available_players = list(range(4000, 4020))

        # Создаем структуру с предсказанным количеством линий
        placement = [[] for _ in range(predicted_lines)]
        used_players = set()

        # Обязательно ставим вратаря в первую линию
        gk_player = self.find_goalkeeper(available_players, {})
        if not gk_player:
            gk_player = available_players[0] if available_players else 4000

        placement[0].append({'id': gk_player, 'position_id': 11})
        used_players.add(gk_player)

        # Декодируем игроков из данных предсказания
        decoded_players = []
        for i in range(0, len(players_data), 3):
            if i + 2 < len(players_data):
                norm_player_id = players_data[i]
                norm_position_id = players_data[i + 1]
                norm_line_num = players_data[i + 2]

                # Денормализация
                player_id_raw = (norm_player_id * 4000) + 3000
                position_id = int(norm_position_id * 120)
                line_num = int(norm_line_num * 5)

                # Находим ближайшего игрока
                best_player = self.find_closest_available_player(
                    player_id_raw, available_players, used_players, {}
                )

                if best_player:
                    # Корректируем линию под предсказанную структуру
                    line_num = max(1, min(predicted_lines - 1, line_num))

                    decoded_players.append({
                        'id': best_player,
                        'position_id': self.correct_position_id(position_id),
                        'line_num': line_num
                    })
                    used_players.add(best_player)

        # Распределяем игроков по линиям согласно предсказанному распределению
        for player_data in decoded_players:
            line_num = player_data['line_num']
            if line_num < len(placement):
                placement[line_num].append({
                    'id': player_data['id'],
                    'position_id': player_data['position_id']
                })

        # Балансируем структуру
        total_players = sum(len(line) for line in placement)
        print(f"Декодировано игроков: {total_players}")

        # Дозаполняем до 11 игроков если нужно
        if total_players < 11:
            remaining = [p for p in available_players if p not in used_players]
            need_more = 11 - total_players

            # Добавляем в линии с наименьшим заполнением
            for i in range(min(need_more, len(remaining))):
                # Находим линию с минимальным заполнением (кроме вратаря)
                line_sizes = [len(placement[j]) for j in range(1, len(placement))]
                if line_sizes:
                    min_line = line_sizes.index(min(line_sizes)) + 1
                    placement[min_line].append({
                        'id': remaining[i],
                        'position_id': self.get_position_for_line(min_line)
                    })

        final_counts = [len(line) for line in placement]
        print(f"Финальная структура: {'-'.join(map(str, final_counts))}")

        return placement

    def decode_placement_simple(self, prediction, club_id, target_date):
        """Простое декодирование для fallback"""
        try:
            available_players = self.get_available_players(club_id, target_date)
            if not available_players:
                available_players = list(range(4000, 4011))

            placement = [[], [], [], []]  # 4 линии по умолчанию
            used_players = set()

            # Вратарь
            gk = available_players[0] if available_players else 4000
            placement[0].append({'id': gk, 'position_id': 11})
            used_players.add(gk)

            # Остальные игроки
            remaining = [p for p in available_players[1:] if p not in used_players][:10]

            # Распределяем по линиям
            for i, player_id in enumerate(remaining):
                line_idx = (i % 3) + 1  # Линии 1, 2, 3
                placement[line_idx].append({
                    'id': player_id,
                    'position_id': self.get_position_for_line(line_idx)
                })

            return placement
        except Exception:
            # Крайний fallback
            return [
                [{'id': 4000, 'position_id': 11}],
                [{'id': 4001, 'position_id': 34}, {'id': 4002, 'position_id': 34}],
                [{'id': 4003, 'position_id': 76}, {'id': 4004, 'position_id': 76}],
                [{'id': 4005, 'position_id': 105}]
            ]

    def train(self):
        """Улучшенное обучение - СОХРАНЯЕМ ЛОГИКУ"""
        print("Подготовка данных...")
        X, y = self.prepare_training_data()

        if len(X) == 0:
            print("Нет данных для обучения!")
            return

        print("Нормализация данных...")
        X_scaled = self.scaler.fit_transform(X)

        # Разделяем на обучающую и тестовую выборки
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42
        )

        print(f"Размер обучающей выборки: {X_train.shape}")
        print(f"Размер тестовой выборки: {X_test.shape}")

        # Строим адаптивную модель
        self.model = self.build_adaptive_model(X_train.shape[1], y_train.shape[1])

        print("Начинаем обучение...")

        # Улучшенные колбэки против переобучения
        callbacks = [
            EarlyStopping(
                patience=10,
                restore_best_weights=True,
                min_delta=0.001,
                monitor='val_loss'
            ),
            ModelCheckpoint(
                'best_lineup_model.h5',
                save_best_only=True,
                monitor='val_loss'
            )
        ]

        # Обучение
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_test, y_test),
            epochs=50,
            batch_size=32,
            callbacks=callbacks,
            verbose=1
        )

        # Сохраняем лучшую модель
        self.model = load_model('best_lineup_model.h5', compile=False)

        # Перекомпилируем
        self.model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )

        # Сохраняем в новом формате
        self.model.save('lineup_prediction_model.keras')

        with open('lineup_scaler.pkl', 'wb') as f:
            pickle.dump(self.scaler, f)

        # Сохраняем информацию о нормализации
        normalization_info = {
            'player_id_min': 3000,
            'player_id_range': 4000,
            'position_id_max': 120,
            'line_max': 4.0
        }

        with open('normalization_info.pkl', 'wb') as f:
            pickle.dump(normalization_info, f)

        print("Обучение завершено!")

        # Оценка на тестовых данных
        test_results = self.model.evaluate(X_test, y_test, verbose=0)
        print(f"Финальная ошибка на тесте: {test_results}")
        print(f"MAE = {test_results[1]:.4f}")

        # Анализ переобучения
        final_train_loss = history.history['loss'][-1]
        final_val_loss = history.history['val_loss'][-1]
        overfitting_ratio = final_val_loss / final_train_loss

        print(f"\nАнализ переобучения:")
        print(f"Training Loss: {final_train_loss:.4f}")
        print(f"Validation Loss: {final_val_loss:.4f}")
        print(f"Overfitting Ratio: {overfitting_ratio:.2f}")

        if overfitting_ratio > 1.5:
            print("⚠️  Обнаружено переобучение! Модель может работать плохо.")
        else:
            print("✅ Переобучения не обнаружено.")

        # График обучения
        try:
            import matplotlib.pyplot as plt
            plt.figure(figsize=(12, 4))

            plt.subplot(1, 2, 1)
            plt.plot(history.history['loss'], label='Training Loss')
            plt.plot(history.history['val_loss'], label='Validation Loss')
            plt.title('Model Loss')
            plt.ylabel('Loss')
            plt.xlabel('Epoch')
            plt.legend()

            # Добавляем вертикальную линию где остановилось обучение
            best_epoch = np.argmin(history.history['val_loss'])
            plt.axvline(x=best_epoch, color='red', linestyle='--', alpha=0.7, label='Best Model')

            plt.subplot(1, 2, 2)
            plt.plot(history.history['mae'], label='Training MAE')
            plt.plot(history.history['val_mae'], label='Validation MAE')
            plt.title('Model MAE')
            plt.ylabel('MAE')
            plt.xlabel('Epoch')
            plt.legend()
            plt.axvline(x=best_epoch, color='red', linestyle='--', alpha=0.7, label='Best Model')

            plt.tight_layout()
            plt.savefig('training_history.png', dpi=300, bbox_inches='tight')
            print("График обучения сохранен в training_history.png")
        except ImportError:
            print("Matplotlib не установлен - график не создан")


if __name__ == "__main__":
    from django.db import models

    predictor = TeamLineupPredictor()
    predictor.train()