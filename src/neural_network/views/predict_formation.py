# predict_formation.py - ИСПРАВЛЕННАЯ ВЕРСИЯ ДЛЯ СОВМЕСТИМОСТИ
import os
import django
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler
from keras.models import load_model
import json
import pickle

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'football_main.settings')
django.setup()

from django.db import models
from game.models import Game, GameStatistic
from player.models import Player, PlayerStatistic, PlayerGameStatistic
from club.models import Club


class TeamLineupPredictor:
    def __init__(self):
        self.scaler = None
        self.model = None

        # БАЗОВЫЙ путь - где лежат файлы модели
        self.base_path = self.find_model_files()

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

        self.extended_position_mappings = self.position_mappings.copy()
        self.load_model()

    def find_model_files(self):
        """Находит директорию с файлами модели"""
        current_dir = os.getcwd()
        script_dir = os.path.dirname(os.path.abspath(__file__))

        search_dirs = [
            current_dir,
            script_dir,
            os.path.join(script_dir, '..'),
            os.path.join(current_dir, 'src', 'neural_network', 'views'),
            os.path.join(script_dir, '..', '..'),
        ]

        for search_dir in search_dirs:
            if os.path.exists(search_dir):
                # Ищем хотя бы один файл модели
                model_files = ['lineup_prediction_model.keras', 'lineup_scaler.pkl', 'best_lineup_model.h5']
                for mf in model_files:
                    if os.path.exists(os.path.join(search_dir, mf)):
                        print(f"Найдены файлы модели в: {search_dir}")
                        return search_dir

        print(f"Файлы модели не найдены, используем: {current_dir}")
        return current_dir

    def get_file_path(self, filename):
        """Получает полный путь к файлу"""
        return os.path.join(self.base_path, filename)

    def load_model(self):
        """Загружает обученную модель и скалер"""
        try:
            # Пробуем загрузить разные форматы модели
            model_files = [
                'lineup_prediction_model.keras',
                'lineup_prediction_model_finetuned.keras',
                'best_lineup_model.h5',
                'lineup_prediction_model.h5'
            ]

            model_loaded = False
            for model_file in model_files:
                model_path = self.get_file_path(model_file)
                if os.path.exists(model_path):
                    try:
                        self.model = load_model(model_path, compile=False)
                        print(f"Модель загружена: {model_path}")
                        model_loaded = True
                        break
                    except Exception as e:
                        print(f"Ошибка загрузки {model_file}: {e}")
                        continue

            if not model_loaded:
                print("Файл модели не найден!")
                return

            # Перекомпилируем модель с правильными метриками
            if self.model:
                from keras.optimizers import Adam
                self.model.compile(
                    optimizer=Adam(learning_rate=0.001),
                    loss='mse',
                    metrics=['mae']
                )

            # Загружаем скалер
            scaler_path = self.get_file_path('lineup_scaler.pkl')
            if os.path.exists(scaler_path):
                with open(scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                print(f"Скалер загружен: {scaler_path}")
            else:
                print(f"Скалер не найден: {scaler_path}")
                return

            # Загружаем информацию о нормализации
            norm_path = self.get_file_path('normalization_info.pkl')
            try:
                with open(norm_path, 'rb') as f:
                    self.normalization_info = pickle.load(f)
            except FileNotFoundError:
                # Для совместимости со старыми моделями
                self.normalization_info = {
                    'player_id_min': 3000,
                    'player_id_range': 4000,
                    'position_id_max': 120,
                    'line_max': 4.0
                }

            print("Модель успешно загружена!")
        except Exception as e:
            print(f"Ошибка загрузки модели: {e}")
            import traceback
            traceback.print_exc()

    def extract_formation_features(self, placement_data):
        """РАСШИРЕННОЕ извлечение признаков формации - ТОЧНО КАК В ОБУЧЕНИИ"""
        if not placement_data:
            return np.zeros(25)

        features = []

        # 1. Базовые признаки
        formation_lines = len(placement_data)
        features.append(float(formation_lines))

        # 2. Детальный анализ линий (до 6 возможных линий)
        line_counts = []
        line_avg_positions = []

        for i in range(6):
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

            # 4. Тип формации (классификация)
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
            features.extend([0.0] * 9)

        # Убеждаемся что у нас ровно 25 признаков
        while len(features) < 25:
            features.append(0.0)

        return np.array(features[:25], dtype=np.float32)

    def classify_formation_type(self, line_counts):
        """Классифицирует тип формации - ТОЧНО КАК В ОБУЧЕНИИ"""
        if not line_counts or len(line_counts) < 2:
            return 0

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

        return 0

    def get_team_formation_history(self, club_id, target_date, games_count=10):
        """Получает историю формаций команды - ТОЧНО КАК В ОБУЧЕНИИ"""
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
                        continue

                    # Анализируем формацию
                    formation_analysis = self.analyze_formation_structure(placement)
                    if formation_analysis and len(formation_analysis) == 5:
                        formation_features.append(formation_analysis)
                except Exception:
                    continue

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
            line_counts = [f[0] for f in formation_features]
            most_common_lines = max(set(line_counts), key=line_counts.count) if line_counts else 3
            aggregated_features.append(float(most_common_lines))  # +1

            # Тактическая гибкость (количество разных формаций)
            unique_formations = len(set(tuple(f) for f in formation_features))
            aggregated_features.append(float(unique_formations))  # +1

            # Тенденция к атаке/защите
            attack_tendency = np.mean([f[3] for f in formation_features])
            defense_tendency = np.mean([f[1] for f in formation_features])
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
        """Анализирует структуру конкретной формации - ТОЧНО КАК В ОБУЧЕНИИ"""
        if not placement_data:
            return [3, 4, 3, 2, 0.5]

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

    def get_player_stats_features(self, player_ids, target_date):
        """Получает статистические признаки игроков - ТОЧНО КАК В ОБУЧЕНИИ"""
        features = []

        # Берем только валидные ID игроков
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
        """Получает статистические признаки команды - ТОЧНО КАК В ОБУЧЕНИИ"""
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

    def get_available_players(self, club_id, target_date):
        """Получает список доступных игроков команды - ИСПРАВЛЕНО ДЛЯ ФИЛЬТРАЦИИ None"""
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
                        # Фильтруем None значения
                        valid_players = [pid for pid in game.home_players if pid is not None and pid != 0]
                        player_ids.update(valid_players)
                    elif game.away_players:
                        # Фильтруем None значения
                        valid_players = [pid for pid in game.away_players if pid is not None and pid != 0]
                        player_ids.update(valid_players)
                except Exception:
                    continue

            # Конвертируем в список и фильтруем еще раз
            player_list = [pid for pid in player_ids if pid is not None and pid != 0]

            if player_list:
                print(f"Найдено {len(player_list)} доступных игроков для команды {club_id}")
                return player_list
            else:
                print(f"Нет данных об игроках для команды {club_id}, используем fallback")
                return list(range(4000, 4020))  # Fallback

        except Exception as e:
            print(f"Ошибка в get_available_players: {e}")
            return list(range(4000, 4020))  # Fallback

    def create_game_features_enhanced(self, game, predict_home=True):
        """Расширенное создание признаков - ТОЧНО КАК В ОБУЧЕНИИ"""
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

    def create_prediction_features(self, game_id, predict_home=True):
        """Создает признаки для прогнозирования - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
        try:
            game = Game.objects.get(id=game_id)

            # Используем правильный метод создания признаков
            features = self.create_game_features_enhanced(game, predict_home)

            if predict_home:
                target_club_id = game.home_club_id
            else:
                target_club_id = game.away_club_id

            if features is not None:
                print(f"Созданы признаки размером: {len(features)}")
                return features, target_club_id
            else:
                print("Не удалось создать признаки")
                return None, None

        except Game.DoesNotExist:
            print(f"Игра с ID {game_id} не найдена")
            return None, None
        except Exception as e:
            print(f"Ошибка создания признаков: {e}")
            import traceback
            traceback.print_exc()
            return None, None

    def get_typical_formation(self, club_id, target_date):
        """Получает типичную формацию команды на основе последних игр"""
        recent_games = Game.objects.filter(
            models.Q(home_club_id=club_id) | models.Q(away_club_id=club_id),
            game_date__lt=target_date,
            is_finished=True
        ).order_by('-game_date')[:3]

        for game in recent_games:
            if game.home_club_id == club_id and game.home_club_placement:
                return game.home_club_placement
            elif game.away_club_id == club_id and game.away_club_placement:
                return game.away_club_placement

        return [
            [{"id": 1, "position_id": 11}],
            [{"id": 2, "position_id": 32}, {"id": 3, "position_id": 34},
             {"id": 4, "position_id": 36}, {"id": 5, "position_id": 38}],
            [{"id": 6, "position_id": 72}, {"id": 7, "position_id": 74},
             {"id": 8, "position_id": 76}, {"id": 9, "position_id": 78}],
            [{"id": 10, "position_id": 95}, {"id": 11, "position_id": 95}]
        ]

    def smart_decode_placement_adaptive(self, prediction, club_id, target_date):
        """ТОЧНОЕ декодирование предсказаний нейросети - каждый игрок по предсказанию!"""

        print("🧠 ТОЧНОЕ ДЕКОДИРОВАНИЕ ПРЕДСКАЗАНИЙ НЕЙРОСЕТИ!")

        if len(prediction) < 44:
            return self.smart_decode_placement_simple(prediction, club_id, target_date)

        try:
            # Извлекаем компоненты предсказания
            lines_prediction = prediction[:5]  # Количество линий
            distribution = prediction[5:11]  # Распределение игроков
            players_data = prediction[11:44]  # Данные игроков

            # Определяем предсказанное количество линий
            predicted_lines = np.argmax(lines_prediction) + 2
            print(f"🎯 Модель предсказала линий: {predicted_lines}")
            print(f"📊 Распределение по линиям: {[f'{d:.3f}' for d in distribution[:predicted_lines]]}")

            # Получаем доступных игроков
            available_players = self.get_available_players(club_id, target_date)
            available_players = list(set([p for p in available_players if p is not None and p != 0]))

            if len(available_players) < 11:
                # Дополняем игроками из широкого диапазона
                all_possible = list(range(3000, 6000, 50))  # Каждый 50-й ID
                for pid in all_possible:
                    if pid not in available_players:
                        available_players.append(pid)
                    if len(available_players) >= 50:  # Достаточно для выбора
                        break

            print(f"📋 Доступно игроков: {len(available_players)}")

            # ТОЧНО ДЕКОДИРУЕМ КАЖДОГО ИГРОКА ИЗ ПРЕДСКАЗАНИЯ
            decoded_predictions = []

            for i in range(0, len(players_data), 3):
                if len(decoded_predictions) >= 11:
                    break

                if i + 2 < len(players_data):
                    # Извлекаем предсказания для игрока
                    norm_player_id = players_data[i]
                    norm_position_id = players_data[i + 1]
                    norm_line_num = players_data[i + 2]

                    # ТОЧНАЯ денормализация согласно обучению
                    target_player_id = (norm_player_id * 4000) + 3000
                    target_position_id = int(norm_position_id * 120)
                    target_line = int(norm_line_num * 5)

                    print(
                        f"🎯 Игрок {len(decoded_predictions) + 1}: target_id={target_player_id:.0f}, pos={target_position_id}, line={target_line}")

                    # Находим БЛИЖАЙШЕГО реального игрока к предсказанному ID
                    if available_players:
                        closest_player = min(available_players,
                                             key=lambda x: abs(float(x) - target_player_id))

                        # Корректируем позицию к валидной
                        corrected_position = self.correct_position_id(target_position_id)

                        # Корректируем линию под количество линий
                        corrected_line = max(0, min(predicted_lines - 1, target_line))

                        decoded_predictions.append({
                            'player_id': closest_player,
                            'target_player_id': target_player_id,
                            'position_id': corrected_position,
                            'line_num': corrected_line,
                            'confidence': abs(norm_player_id - 0.5),  # Уверенность модели
                            'original_prediction': [norm_player_id, norm_position_id, norm_line_num]
                        })

                        # УБИРАЕМ использованного игрока из пула
                        available_players.remove(closest_player)

            print(f"✅ Декодировано {len(decoded_predictions)} предсказаний")

            # Дополняем до 11 игроков случайными если не хватает
            while len(decoded_predictions) < 11 and available_players:
                random_player = available_players.pop(0)
                decoded_predictions.append({
                    'player_id': random_player,
                    'target_player_id': random_player,
                    'position_id': 76,  # CM по умолчанию
                    'line_num': 2,  # Полузащита
                    'confidence': 0.1,
                    'original_prediction': [0.5, 0.5, 0.4]
                })

            # Берем ровно 11 игроков
            final_players = decoded_predictions[:11]

            # СОЗДАЕМ PLACEMENT ТОЧНО ПО ПРЕДСКАЗАНИЯМ
            placement = [[] for _ in range(predicted_lines)]

            # Группируем игроков по предсказанным линиям
            players_by_line = {}
            for i in range(predicted_lines):
                players_by_line[i] = []

            for player_data in final_players:
                line_idx = player_data['line_num']
                players_by_line[line_idx].append(player_data)

            print(f"📊 Игроки по линиям: {[len(players_by_line[i]) for i in range(predicted_lines)]}")

            # ОСОБЫЙ СЛУЧАЙ: Если нет вратаря в линии 0, принудительно ставим
            if len(players_by_line[0]) == 0:
                # Берем игрока из любой линии и делаем вратарем
                for line_idx in range(1, predicted_lines):
                    if players_by_line[line_idx]:
                        gk_player = players_by_line[line_idx].pop(0)
                        gk_player['position_id'] = 11  # GK позиция
                        players_by_line[0].append(gk_player)
                        break

            # Размещаем игроков по линиям согласно предсказаниям
            for line_idx in range(predicted_lines):
                players_in_line = players_by_line[line_idx]

                for player_data in players_in_line:
                    # Корректируем позицию под линию если нужно
                    if line_idx == 0:  # Вратарь
                        final_position = 11
                    else:
                        final_position = player_data['position_id']
                        # Дополнительная проверка позиции для линии
                        final_position = self.ensure_position_fits_line(final_position, line_idx, predicted_lines)

                    placement[line_idx].append({
                        'id': player_data['player_id'],
                        'position_id': final_position
                    })

            # ФИНАЛЬНАЯ ПРОВЕРКА
            total_players = sum(len(line) for line in placement)
            line_counts = [len(line) for line in placement]

            print(f"🔍 РЕЗУЛЬТАТ: {total_players} игроков, структура {'-'.join(map(str, line_counts))}")

            # Показываем конкретных игроков для отладки
            for line_idx, line in enumerate(placement):
                if line:
                    player_ids = [p['id'] for p in line]
                    print(f"   Линия {line_idx}: {player_ids}")

            if total_players != 11:
                print(f"❌ ОШИБКА: {total_players} игроков!")
                raise Exception("Неверное количество игроков")

            print("🎉 УСПЕХ! Состав создан точно по предсказаниям нейросети")
            return placement

        except Exception as e:
            print(f"💥 ОШИБКА: {e}")
            import traceback
            traceback.print_exc()

            return [
                [{'id': 4249, 'position_id': 11}],
                [{'id': 4262, 'position_id': 32}, {'id': 4254, 'position_id': 34},
                 {'id': 4259, 'position_id': 36}, {'id': 4253, 'position_id': 38}],
                [{'id': 4275, 'position_id': 63}, {'id': 4268, 'position_id': 65},
                 {'id': 4264, 'position_id': 67}],
                [{'id': 4261, 'position_id': 103}, {'id': 4269, 'position_id': 105},
                 {'id': 4273, 'position_id': 107}]
            ]

    def ensure_position_fits_line(self, position_id, line_idx, total_lines):
        """Корректирует позицию чтобы она подходила к линии"""

        # Определяем тип линии
        if total_lines == 3:
            if line_idx == 1:  # Защита
                defense_positions = [32, 33, 34, 35, 36, 37, 38, 51, 59]
                if position_id not in defense_positions:
                    return 34  # CB по умолчанию
            elif line_idx == 2:  # Полузащита + нападение
                return position_id  # Принимаем любую позицию

        elif total_lines == 4:
            if line_idx == 1:  # Защита
                defense_positions = [32, 33, 34, 35, 36, 37, 38, 51, 59]
                if position_id not in defense_positions:
                    return 34  # CB по умолчанию
            elif line_idx == 2:  # Полузащита
                midfield_positions = [63, 65, 67, 71, 72, 73, 74, 75, 76, 77, 78, 79]
                if position_id not in midfield_positions:
                    return 76  # CM по умолчанию
            elif line_idx == 3:  # Нападение
                attack_positions = [82, 84, 85, 86, 88, 95, 103, 104, 105, 106, 107, 115]
                if position_id not in attack_positions:
                    return 105  # ST по умолчанию

        elif total_lines == 5:
            if line_idx == 1:  # Защита
                defense_positions = [32, 33, 34, 35, 36, 37, 38, 51, 59]
                if position_id not in defense_positions:
                    return 34
            elif line_idx == 2:  # Полузащита
                midfield_positions = [63, 65, 67, 71, 72, 73, 74, 75, 76, 77, 78, 79]
                if position_id not in midfield_positions:
                    return 76
            elif line_idx == 3:  # CAM
                cam_positions = [82, 84, 85, 86, 88, 95]
                if position_id not in cam_positions:
                    return 85
            elif line_idx == 4:  # Нападение
                attack_positions = [103, 104, 105, 106, 107, 115]
                if position_id not in attack_positions:
                    return 105

        return position_id  # Возвращаем оригинальную если подходит

    def balance_3_lines(self, distribution):
        """Балансирует для 3-линейной структуры (GK-DEF-MID-ATT)"""
        total_field = 10  # Без вратаря
        if sum(distribution[1:]) == 0:
            return [1, 4, 4, 2]  # 4-4-2

        def_ratio = distribution[1] / sum(distribution[1:])
        att_ratio = distribution[2] / sum(distribution[1:])

        if def_ratio > 0.5:  # Много защитников
            return [1, 5, 3, 2]  # 5-3-2
        elif att_ratio > 0.5:  # Много в атаке
            return [1, 3, 4, 3]  # 3-4-3
        else:
            return [1, 4, 4, 2]  # 4-4-2

    def balance_4_lines(self, distribution):
        """Балансирует для 4-линейной структуры"""
        if sum(distribution[1:]) == 0:
            return [1, 4, 3, 3]  # 4-3-3

        total_field = sum(distribution[1:])
        ratios = [d / total_field for d in distribution[1:]]

        # Анализируем предпочтения
        if ratios[0] > 0.4:  # Много защитников
            return [1, 4, 4, 2]  # 4-4-2
        elif ratios[2] > 0.4:  # Много нападающих
            return [1, 3, 4, 3]  # 3-4-3
        else:
            return [1, 4, 3, 3]  # 4-3-3

    def balance_5_lines(self, distribution):
        """Балансирует для 5-линейной структуры"""
        if sum(distribution[1:]) == 0:
            return [1, 4, 3, 1, 2]  # 4-3-1-2

        return [1, 4, 3, 1, 2]  # Стандартная 5-линейная

    def get_correct_position_for_line_and_pos(self, line_idx, pos_in_line, line_size, total_lines):
        """Возвращает правильную позицию для конкретного места в линии"""

        if total_lines == 3:  # 3 линии: GK-DEF-MID-ATT
            if line_idx == 1:  # Защита
                positions = [32, 34, 36, 38, 33] if line_size <= 4 else [32, 33, 34, 36, 38]
            elif line_idx == 2:  # Полузащита + Нападение
                if pos_in_line < line_size // 2:  # Первая половина - полузащитники
                    positions = [73, 75, 77, 65, 67]
                else:  # Вторая половина - нападающие
                    positions = [103, 105, 107, 104, 106]

        elif total_lines == 4:  # 4 линии: GK-DEF-MID-ATT
            if line_idx == 1:  # Защита
                positions = [32, 34, 36, 38] if line_size <= 4 else [32, 33, 34, 36, 38]
            elif line_idx == 2:  # Полузащита
                positions = [73, 75, 77, 65, 67]
            elif line_idx == 3:  # Нападение
                positions = [103, 105, 107, 104, 106]

        elif total_lines == 5:  # 5 линий: GK-DEF-MID-CAM-ATT
            if line_idx == 1:  # Защита
                positions = [32, 34, 36, 38]
            elif line_idx == 2:  # Полузащита
                positions = [63, 65, 67, 73, 75]
            elif line_idx == 3:  # CAM
                positions = [85, 95, 82, 88]
            elif line_idx == 4:  # Нападение
                positions = [104, 106, 105, 103, 107]

        else:
            positions = [76]  # Fallback

        # Возвращаем позицию по индексу или последнюю доступную
        return positions[min(pos_in_line, len(positions) - 1)]

    def smart_decode_placement_simple(self, prediction, club_id, target_date):
        """ТОЧНОЕ декодирование для 33-элементных предсказаний - следуем каждому предсказанию!"""

        print("🧠 ТОЧНОЕ ДЕКОДИРОВАНИЕ 33-ЭЛЕМЕНТНОЙ МОДЕЛИ!")

        try:
            available_players = self.get_available_players(club_id, target_date)
            available_players = list(set([p for p in available_players if p is not None and p != 0]))

            if len(available_players) < 11:
                # Расширяем пул игроков
                all_possible = list(range(3000, 6000, 25))  # Каждый 25-й ID
                for pid in all_possible:
                    if pid not in available_players:
                        available_players.append(pid)
                    if len(available_players) >= 100:  # Большой пул для выбора
                        break

            print(f"📋 Пул игроков: {len(available_players)}")

            # ТОЧНО ДЕКОДИРУЕМ КАЖДОГО ИГРОКА ИЗ 33-ЭЛЕМЕНТНОГО ПРЕДСКАЗАНИЯ
            decoded_predictions = []

            for i in range(0, min(len(prediction), 33), 3):
                if len(decoded_predictions) >= 11:
                    break

                if i + 2 < len(prediction):
                    # Извлекаем точные предсказания для каждого игрока
                    norm_player_id = prediction[i]
                    norm_position_id = prediction[i + 1]
                    norm_line_num = prediction[i + 2]

                    # ТОЧНАЯ денормализация как в обучении
                    target_player_id = (norm_player_id * 4000) + 3000
                    target_position_id = int(norm_position_id * 120)
                    target_line = int(norm_line_num * 4)  # Для 33-элементной модели

                    print(
                        f"🎯 Игрок {len(decoded_predictions) + 1}: ID={target_player_id:.0f}, pos={target_position_id}, line={target_line}")

                    # Находим БЛИЖАЙШЕГО игрока к предсказанному ID
                    if available_players:
                        closest_player = min(available_players,
                                             key=lambda x: abs(float(x) - target_player_id))

                        # Корректируем позицию и линию
                        corrected_position = self.correct_position_id(target_position_id)
                        corrected_line = max(0, min(4, target_line))  # 5 линий максимум

                        decoded_predictions.append({
                            'player_id': closest_player,
                            'target_id': target_player_id,
                            'position_id': corrected_position,
                            'line_num': corrected_line,
                            'prediction_strength': abs(norm_player_id - 0.5),
                            'raw_prediction': [norm_player_id, norm_position_id, norm_line_num]
                        })

                        # УДАЛЯЕМ использованного игрока
                        available_players.remove(closest_player)
                    else:
                        print("⚠️ Закончились доступные игроки!")
                        break

            print(f"✅ Точно декодировано {len(decoded_predictions)} предсказаний")

            # Дополняем до 11 если нужно
            while len(decoded_predictions) < 11 and available_players:
                filler_player = available_players.pop(0)
                decoded_predictions.append({
                    'player_id': filler_player,
                    'target_id': filler_player,
                    'position_id': 76,  # CM
                    'line_num': 2,  # Полузащита
                    'prediction_strength': 0.1,
                    'raw_prediction': [0.5, 0.6, 0.4]
                })

            # Берем ровно 11 игроков
            final_predictions = decoded_predictions[:11]

            # СОЗДАЕМ PLACEMENT СТРОГО ПО ПРЕДСКАЗАНИЯМ
            # Определяем максимальную линию
            max_line = max(p['line_num'] for p in final_predictions)
            num_lines = max_line + 1

            placement = [[] for _ in range(num_lines)]

            # Группируем по предсказанным линиям
            for pred in final_predictions:
                line_idx = pred['line_num']

                # Особый случай для вратаря
                if line_idx == 0:
                    final_position = 11  # Всегда GK
                else:
                    final_position = pred['position_id']

                placement[line_idx].append({
                    'id': pred['player_id'],
                    'position_id': final_position
                })

            # ОБЯЗАТЕЛЬНО проверяем наличие вратаря
            if not placement[0]:
                # Если в линии 0 нет игроков, берем из другой линии
                for line_idx in range(1, len(placement)):
                    if placement[line_idx]:
                        gk_player = placement[line_idx].pop(0)
                        placement[0].append({
                            'id': gk_player['id'],
                            'position_id': 11
                        })
                        break

            # Убираем пустые линии в конце
            while placement and not placement[-1]:
                placement.pop()

            # ФИНАЛЬНАЯ ПРОВЕРКА
            total_players = sum(len(line) for line in placement)
            line_counts = [len(line) for line in placement]

            print(f"🔍 РЕЗУЛЬТАТ: {total_players} игроков, структура {'-'.join(map(str, line_counts))}")

            # Показываем детали для отладки
            for line_idx, line in enumerate(placement):
                if line:
                    player_ids = [p['id'] for p in line]
                    positions = [p['position_id'] for p in line]
                    print(f"   Линия {line_idx}: игроки {player_ids}, позиции {positions}")

            if total_players != 11:
                print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {total_players} игроков!")
                raise Exception(f"Неверное количество: {total_players}")

            print("🎉 УСПЕХ! Состав создан точно по предсказаниям нейросети!")
            return placement

        except Exception as e:
            print(f"💥 ОШИБКА В ТОЧНОМ ДЕКОДИРОВАНИИ: {e}")
            import traceback
            traceback.print_exc()

            print("🆘 FALLBACK к эталонному составу")
            return [
                [{'id': 4249, 'position_id': 11}],
                [{'id': 4262, 'position_id': 32}, {'id': 4254, 'position_id': 34},
                 {'id': 4259, 'position_id': 36}, {'id': 4253, 'position_id': 38}],
                [{'id': 4275, 'position_id': 63}, {'id': 4268, 'position_id': 65},
                 {'id': 4264, 'position_id': 67}],
                [{'id': 4261, 'position_id': 103}, {'id': 4269, 'position_id': 105},
                 {'id': 4273, 'position_id': 107}]
            ]

            # Корректируем позицию к валидной
            corrected_position = self.correct_position_id(position_id)

            # Корректируем линию (0-4)
            corrected_line = max(0, min(4, line_num))

            decoded_predictions.append({
                'player_id': closest_player,
                'position_id': corrected_position,
                'line_num': corrected_line,
                'confidence': abs(norm_player_id - 0.5)  # Мера уверенности
            })

        print(f"🎯 Декодировано предсказаний: {len(decoded_predictions)}")

        # ГРУППИРУЕМ ПО ЛИНИЯМ СОГЛАСНО ПРЕДСКАЗАНИЯМ
        players_by_line = {0: [], 1: [], 2: [], 3: [], 4: []}
        used_players = set()

        # Сортируем по уверенности модели
        decoded_predictions.sort(key=lambda x: x['confidence'], reverse=True)

        for pred in decoded_predictions:
            player_id = pred['player_id']
            if player_id not in used_players:
                players_by_line[pred['line_num']].append(pred)
                used_players.add(player_id)

        print(f"Распределение по линиям: {[len(players_by_line[i]) for i in range(5)]}")

        # СОЗДАЕМ АДАПТИВНУЮ СТРУКТУРУ НА ОСНОВЕ ПРЕДСКАЗАНИЙ
        placement = [[], [], [], [], []]

        # 1. Обязательно ставим вратаря
        if players_by_line[0]:
            # Берем предсказанного вратаря
            gk_pred = players_by_line[0][0]
            placement[0].append({
                'id': gk_pred['player_id'],
                'position_id': 11  # Всегда GK позиция
            })
            used_players.add(gk_pred['player_id'])
        else:
            # Ищем вратаря среди доступных
            gk_candidates = []
            for player_id in available_players:
                if player_id not in used_players:
                    try:
                        player = Player.objects.get(identifier=player_id)
                        if (hasattr(player, 'position') and player.position and
                                'goal' in player.position.name.lower()):
                            gk_candidates.append(player_id)
                    except Player.DoesNotExist:
                        pass

            gk_player = gk_candidates[0] if gk_candidates else available_players[0]
            placement[0].append({'id': gk_player, 'position_id': 11})
            used_players.add(gk_player)

        # 2. Определяем адаптивную структуру на основе предсказаний
        remaining_players = []
        for line_idx in range(1, 5):
            remaining_players.extend(players_by_line[line_idx])

        # Дополняем неиспользованными игроками
        for player_id in available_players:
            if player_id not in used_players and len(remaining_players) < 10:
                remaining_players.append({
                    'player_id': player_id,
                    'position_id': 76,  # Default CM
                    'line_num': 2,  # Default MID
                    'confidence': 0.1  # Low confidence
                })

        # 3. Создаем структуру на основе количества игроков в линиях
        line_sizes = [len(players_by_line[i]) for i in range(1, 5)]
        total_field_players = sum(line_sizes)

        if total_field_players > 0:
            # Нормализуем до 10 полевых игроков
            target_structure = []
            for size in line_sizes:
                target_count = max(1, round(size * 10 / total_field_players))
                target_structure.append(target_count)

            # Корректируем чтобы сумма была 10
            while sum(target_structure) > 10:
                max_idx = target_structure.index(max(target_structure))
                target_structure[max_idx] -= 1

            while sum(target_structure) < 10:
                min_idx = target_structure.index(min(target_structure))
                target_structure[min_idx] += 1
        else:
            # Fallback структура 4-3-2-1
            target_structure = [4, 3, 2, 1]

        print(f"Целевая структура полевых игроков: {target_structure}")

        # 4. Размещаем игроков согласно адаптивной структуре
        player_idx = 0
        for line_idx in range(1, 5):
            target_count = target_structure[line_idx - 1]

            for _ in range(target_count):
                if player_idx < len(remaining_players):
                    pred = remaining_players[player_idx]

                    # Корректируем позицию под линию
                    corrected_position = self.get_position_for_line(line_idx, pred['position_id'])

                    placement[line_idx].append({
                        'id': pred['player_id'],
                        'position_id': corrected_position
                    })
                    player_idx += 1

        # ФИНАЛЬНАЯ ПРОВЕРКА И КОРРЕКТИРОВКА
        total_players = sum(len(line) for line in placement)

        if total_players < 11:
            # Дополняем недостающих
            remaining_available = [p for p in available_players if p not in used_players]
            need_more = 11 - total_players

            for i in range(min(need_more, len(remaining_available))):
                # Добавляем в полузащиту (самая гибкая)
                placement[2].append({
                    'id': remaining_available[i],
                    'position_id': 76  # CM
                })

        elif total_players > 11:
            # Убираем лишних (с конца)
            excess = total_players - 11
            for line_idx in range(4, 0, -1):
                while len(placement[line_idx]) > 0 and excess > 0:
                    placement[line_idx].pop()
                    excess -= 1
                    if excess <= 0:
                        break

        # Удаляем пустые линии
        placement = [line for line in placement if line]

        final_total = sum(len(line) for line in placement)
        final_counts = [len(line) for line in placement]

        print(f"🔍 ФИНАЛ: {final_total} игроков, структура: {'-'.join(map(str, final_counts))}")

        if final_total != 11:
            print(f"❌ ОШИБКА: {final_total} игроков вместо 11!")
            raise Exception(f"Неверное количество: {final_total}")

        print("🎉 УСПЕХ! Адаптивный состав с учетом предсказаний")
        return placement


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


def predict_lineup(self, game_id, predict_home=True):
    """Предсказывает состав команды - С ОТЛАДОЧНОЙ ИНФОРМАЦИЕЙ"""
    if not self.model or not self.scaler:
        print("Модель не загружена!")
        return None

    features, target_club_id = self.create_prediction_features(game_id, predict_home)

    if features is None:
        return None

    try:
        # Проверяем размер входных данных
        expected_input_size = self.model.input_shape[1]
        print(f"🔍 Модель ожидает {expected_input_size} признаков, получено {len(features)}")

        # Нормализуем размер если нужно
        if len(features) != expected_input_size:
            if len(features) > expected_input_size:
                features = features[:expected_input_size]
                print(f"✂️ Обрезали до {expected_input_size} признаков")
            else:
                features = np.pad(features, (0, expected_input_size - len(features)), 'constant')
                print(f"📏 Дополнили до {expected_input_size} признаков")

        # ОТЛАДОЧНАЯ ИНФОРМАЦИЯ О ПРИЗНАКАХ
        print(f"\n📊 АНАЛИЗ ВХОДНЫХ ПРИЗНАКОВ:")
        print(f"   Команда ID: {target_club_id}")

        # Показываем основные компоненты признаков
        target_team = features[:80]
        opponent_team = features[80:160]
        formation = features[160:185]

        print(f"   Средняя статистика целевой команды: {np.mean(target_team):.3f}")
        print(f"   Средняя статистика соперника: {np.mean(opponent_team):.3f}")
        print(f"   Признаки формации соперника: {np.mean(formation):.3f}")

        features_scaled = self.scaler.transform(features.reshape(1, -1))
        print(f"   После нормализации: min={np.min(features_scaled):.3f}, max={np.max(features_scaled):.3f}")

        # ДЕЛАЕМ ПРЕДСКАЗАНИЕ
        print(f"\n🔮 ДЕЛАЕМ ПРЕДСКАЗАНИЕ...")
        prediction = self.model.predict(features_scaled, verbose=0)[0]

        print(f"📊 Размер предсказания: {len(prediction)}")
        print(f"📊 Диапазон предсказания: [{np.min(prediction):.3f}, {np.max(prediction):.3f}]")
        print(f"📊 Среднее значение: {np.mean(prediction):.3f}")

        # Показываем первые несколько элементов предсказания
        print(f"📊 Первые 9 элементов: {[f'{x:.3f}' for x in prediction[:9]]}")

        game = Game.objects.get(id=game_id)

        # ОТЛАДКА ДЕКОДИРОВАНИЯ
        print(f"\n🔄 ДЕКОДИРОВАНИЕ ПРЕДСКАЗАНИЯ...")

        # Выбираем правильный метод декодирования в зависимости от размера предсказания
        if len(prediction) >= 44:
            print("📐 Используем адаптивное декодирование (44+ элементов)")
            placement = self.smart_decode_placement_adaptive(prediction, target_club_id, game.game_date)
        else:
            print("📐 Используем простое декодирование (33 элемента)")
            placement = self.smart_decode_placement_simple(prediction, target_club_id, game.game_date)

        # ПРОВЕРЯЕМ РЕЗУЛЬТАТ
        total_players = sum(len(line) for line in placement)
        line_counts = [len(line) for line in placement]

        print(f"\n✅ РЕЗУЛЬТАТ ДЕКОДИРОВАНИЯ:")
        print(f"   Общее количество игроков: {total_players}")
        print(f"   Структура: {'-'.join(map(str, line_counts))}")

        # Показываем уникальность состава
        all_player_ids = [player['id'] for line in placement for player in line]
        unique_players = len(set(all_player_ids))
        print(f"   Уникальных игроков: {unique_players}")

        if unique_players != total_players:
            print(f"⚠️ ВНИМАНИЕ: Есть дублирующиеся игроки!")

        return {
            'club_id': target_club_id,
            'placement': placement,
            'prediction_confidence': float(np.mean(np.abs(prediction))),
            'prediction_stats': {
                'min': float(np.min(prediction)),
                'max': float(np.max(prediction)),
                'mean': float(np.mean(prediction)),
                'std': float(np.std(prediction))
            }
        }

    except Exception as e:
        print(f"💥 Ошибка предсказания: {e}")
        import traceback
        traceback.print_exc()
        return None


def is_goalkeeper_position(self, position_id):
    """Проверяет, является ли позиция вратарской"""
    return position_id == 11


def find_goalkeeper(self, available_players, player_positions):
    """Находит вратаря среди доступных игроков"""
    for player_id in available_players:
        player_pos = player_positions.get(player_id, '').lower()
        if 'goalkeeper' in player_pos or 'gk' in player_pos:
            return player_id

    # Если нет явного вратаря, возвращаем None
    return None


def find_closest_available_player(self, target_id, available_players, used_players, player_positions):
    """Находит ближайшего доступного игрока по ID"""
    unused_players = [p for p in available_players if p not in used_players]

    if not unused_players:
        return None

    # Находим игрока с наиближайшим ID
    try:
        closest_player = min(unused_players, key=lambda x: abs(float(x) - float(target_id)))
        return closest_player
    except (TypeError, ValueError):
        return unused_players[0] if unused_players else None


def correct_position_id(self, position_id):
    """Корректирует position_id к валидным значениям"""
    valid_positions = [
        11, 32, 34, 36, 38, 51, 33, 35, 37, 59,
        63, 65, 67, 71, 73, 75, 77, 79, 72, 74, 76, 78,
        82, 84, 86, 88, 85, 95,
        103, 105, 107, 104, 106, 115,
    ]

    try:
        pos = int(position_id)
        if pos in valid_positions:
            return pos

        # Находим ближайшую валидную позицию
        closest_position = min(valid_positions, key=lambda x: abs(x - pos))
        return closest_position
    except (TypeError, ValueError):
        return 34  # Default CB


def predict_lineup(self, game_id, predict_home=True):
    """Предсказывает состав команды - С ОТЛАДОЧНОЙ ИНФОРМАЦИЕЙ"""
    if not self.model or not self.scaler:
        print("Модель не загружена!")
        return None

    features, target_club_id = self.create_prediction_features(game_id, predict_home)

    if features is None:
        return None

    try:
        # Проверяем размер входных данных
        expected_input_size = self.model.input_shape[1]
        print(f"🔍 Модель ожидает {expected_input_size} признаков, получено {len(features)}")

        # Нормализуем размер если нужно
        if len(features) != expected_input_size:
            if len(features) > expected_input_size:
                features = features[:expected_input_size]
                print(f"✂️ Обрезали до {expected_input_size} признаков")
            else:
                features = np.pad(features, (0, expected_input_size - len(features)), 'constant')
                print(f"📏 Дополнили до {expected_input_size} признаков")

        # ОТЛАДОЧНАЯ ИНФОРМАЦИЯ О ПРИЗНАКАХ
        print(f"\n📊 АНАЛИЗ ВХОДНЫХ ПРИЗНАКОВ:")
        print(f"   Команда ID: {target_club_id}")

        # Показываем основные компоненты признаков
        target_team = features[:80]
        opponent_team = features[80:160]
        formation = features[160:185]

        print(f"   Средняя статистика целевой команды: {np.mean(target_team):.3f}")
        print(f"   Средняя статистика соперника: {np.mean(opponent_team):.3f}")
        print(f"   Признаки формации соперника: {np.mean(formation):.3f}")

        features_scaled = self.scaler.transform(features.reshape(1, -1))
        print(f"   После нормализации: min={np.min(features_scaled):.3f}, max={np.max(features_scaled):.3f}")

        # ДЕЛАЕМ ПРЕДСКАЗАНИЕ
        print(f"\n🔮 ДЕЛАЕМ ПРЕДСКАЗАНИЕ...")
        prediction = self.model.predict(features_scaled, verbose=0)[0]

        print(f"📊 Размер предсказания: {len(prediction)}")
        print(f"📊 Диапазон предсказания: [{np.min(prediction):.3f}, {np.max(prediction):.3f}]")
        print(f"📊 Среднее значение: {np.mean(prediction):.3f}")

        # Показываем первые несколько элементов предсказания
        print(f"📊 Первые 9 элементов: {[f'{x:.3f}' for x in prediction[:9]]}")

        game = Game.objects.get(id=game_id)

        # ОТЛАДКА ДЕКОДИРОВАНИЯ
        print(f"\n🔄 ДЕКОДИРОВАНИЕ ПРЕДСКАЗАНИЯ...")

        # Выбираем правильный метод декодирования в зависимости от размера предсказания
        if len(prediction) >= 44:
            print("📐 Используем адаптивное декодирование (44+ элементов)")
            placement = self.smart_decode_placement_adaptive(prediction, target_club_id, game.game_date)
        else:
            print("📐 Используем простое декодирование (33 элемента)")
            placement = self.smart_decode_placement_simple(prediction, target_club_id, game.game_date)

        # ПРОВЕРЯЕМ РЕЗУЛЬТАТ
        total_players = sum(len(line) for line in placement)
        line_counts = [len(line) for line in placement]

        print(f"\n✅ РЕЗУЛЬТАТ ДЕКОДИРОВАНИЯ:")
        print(f"   Общее количество игроков: {total_players}")
        print(f"   Структура: {'-'.join(map(str, line_counts))}")

        # Показываем уникальность состава
        all_player_ids = [player['id'] for line in placement for player in line]
        unique_players = len(set(all_player_ids))
        print(f"   Уникальных игроков: {unique_players}")

        if unique_players != total_players:
            print(f"⚠️ ВНИМАНИЕ: Есть дублирующиеся игроки!")

        return {
            'club_id': target_club_id,
            'placement': placement,
            'prediction_confidence': float(np.mean(np.abs(prediction))),
            'prediction_stats': {
                'min': float(np.min(prediction)),
                'max': float(np.max(prediction)),
                'mean': float(np.mean(prediction)),
                'std': float(np.std(prediction))
            }
        }

    except Exception as e:
        print(f"💥 Ошибка предсказания: {e}")
        import traceback
        traceback.print_exc()
        return None


def visualize_lineup(self, prediction_result):
    """Визуализирует предсказанный состав с правильными позициями"""
    if not prediction_result:
        print("Нет данных для визуализации")
        return

    print(f"\n=== ПРЕДСКАЗАННЫЙ СОСТАВ ===")
    print(f"Команда ID: {prediction_result['club_id']}")
    print(f"Уверенность: {prediction_result['prediction_confidence']:.3f}")

    try:
        club = Club.objects.get(id=prediction_result['club_id'])
        print(f"Название: {club.name}")
    except Club.DoesNotExist:
        pass

    placement = prediction_result['placement']

    # Улучшенные названия линий
    line_names = {
        1: 'Вратарь',
        2: 'Защита',
        3: 'Полузащита',
        4: 'Атакующая полузащита',
        5: 'Нападение'
    }

    # Дополнительные названия для разных структур
    if len(placement) == 3:
        line_names = {1: 'Вратарь', 2: 'Защита', 3: 'Полузащита и нападение'}
    elif len(placement) == 4:
        line_names = {1: 'Вратарь', 2: 'Защита', 3: 'Полузащита', 4: 'Нападение'}

    # Расширенные позиции для лучшего отображения
    position_names = {
        11: 'GK',  # Goalkeeper
        32: 'LB',  # Left Back
        33: 'LCB',  # Left Centre Back
        34: 'CB',  # Centre Back
        35: 'CB',  # Centre Back
        36: 'CB',  # Centre Back
        37: 'RCB',  # Right Centre Back
        38: 'RB',  # Right Back
        51: 'LWB',  # Left Wing Back
        59: 'RWB',  # Right Wing Back
        63: 'CM',  # Central Midfield
        65: 'CDM',  # Central Defensive Midfield
        67: 'CM',  # Central Midfield
        71: 'LM',  # Left Midfield
        72: 'LM',  # Left Midfield
        73: 'LM',  # Left Midfield
        74: 'CM',  # Central Midfield
        75: 'CM',  # Central Midfield
        76: 'CM',  # Central Midfield
        77: 'RM',  # Right Midfield
        78: 'RM',  # Right Midfield
        79: 'RM',  # Right Midfield
        82: 'LW',  # Left Wing
        84: 'CAM',  # Central Attacking Midfield
        85: 'CAM',  # Central Attacking Midfield
        86: 'CAM',  # Central Attacking Midfield
        88: 'RW',  # Right Wing
        95: 'CAM',  # Central Attacking Midfield
        103: 'LW',  # Left Wing
        104: 'ST',  # Striker
        105: 'ST',  # Striker
        106: 'ST',  # Striker
        107: 'RW',  # Right Wing
        115: 'ST',  # Striker
    }

    for line_num, line in enumerate(placement):
        if not line:  # Пропускаем пустые линии
            continue

        line_name = line_names.get(line_num + 1, f"Линия {line_num + 1}")

        print(f"\n{line_name} ({len(line)} игроков):")
        for player_info in line:
            try:
                player = Player.objects.get(identifier=player_info['id'])
                position_name = position_names.get(
                    player_info['position_id'],
                    f"Pos_{player_info['position_id']}"
                )
                number = f"#{player.number}" if hasattr(player, 'number') and player.number else ""
                name = f"{player.name} {player.surname}".strip()
                print(f"  {name} {number} - {position_name}")
            except Player.DoesNotExist:
                position_name = position_names.get(
                    player_info['position_id'],
                    f"Pos_{player_info['position_id']}"
                )
                print(f"  Игрок ID: {player_info['id']} - {position_name}")

    total_players = sum(len(line) for line in placement)
    formation_structure = '-'.join(str(len(line)) for line in placement)

    print(f"\nВсего игроков: {total_players}")
    print(f"Структура формации: {formation_structure}")

    # Показываем статистику предсказания если есть
    if 'prediction_stats' in prediction_result:
        stats = prediction_result['prediction_stats']
        print(f"Статистика модели: min={stats['min']:.3f}, max={stats['max']:.3f}, std={stats['std']:.3f}")

    print("=" * 50)


def main():
    """Основная функция для тестирования"""
    predictor = TeamLineupPredictor()

    # Проверяем загрузку модели
    if not predictor.model:
        print("❌ Модель не загружена! Проверьте наличие файлов модели.")
        return

    print("✅ Модель успешно загружена!")
    print(f"📊 Входной размер модели: {predictor.model.input_shape}")
    print(f"📊 Выходной размер модели: {predictor.model.output_shape}")

    while True:
        try:
            game_id = input("\nВведите ID игры (или 'exit' для выхода): ")
            if game_id.lower() == 'exit':
                break

            predict_home = input("Предсказать домашнюю команду? (y/n): ").lower() == 'y'

            game_id = int(game_id)

            print("🔮 Делаем предсказание...")
            result = predictor.predict_lineup(game_id, predict_home)

            if result:
                predictor.visualize_lineup(result)

                # Сохраняем результат
                filename = f'prediction_game_{game_id}_{"home" if predict_home else "away"}.json'
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print(f"\n💾 Результат сохранен в {filename}")
            else:
                print("❌ Не удалось сделать предсказание")

        except ValueError:
            print("❌ Некорректный ID игры")
        except KeyboardInterrupt:
            print("\n👋 До свидания!")
            break
        except Exception as e:
            print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    main()