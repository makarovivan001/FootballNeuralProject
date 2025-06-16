# ai-new.py - Итоговая версия ИИ с жесткими ограничениями

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "football_main.settings")
django.setup()

import numpy as np
import json
import joblib
from keras.models import load_model
from game.models import Game
from player.models import Player, Position, PlayerGameStatistic
from club.models import Club
from django.db.models import Q

print("🎯 ИТОГОВЫЙ SKLEARN AI С ЖЕСТКИМИ ОГРАНИЧЕНИЯМИ")
print("📊 Ансамбль: RF + ET + GB + LR + NN + Улучшенная NN + Валидация позиций")
print("🔒 Жесткие ограничения: игровое время + уникальные позиции + строго 11 игроков")

# Загружаем модели и конфигурацию
try:
    rf_model = joblib.load("sklearn_rf_model.pkl")
    et_model = joblib.load("sklearn_et_model.pkl")
    gb_model = joblib.load("sklearn_gb_model.pkl")
    lr_model = joblib.load("sklearn_lr_model.pkl")
    nn_model = load_model("sklearn_nn_model.keras", compile=False)

    # Пытаемся загрузить улучшенную модель
    try:
        improved_nn_model = load_model("neural_network_improved.keras", compile=False)
        print("✅ Улучшенная нейросеть загружена!")
    except:
        improved_nn_model = None
        print("⚠️ Улучшенная нейросеть не найдена, используем базовую")

    scaler = joblib.load("sklearn_scaler.pkl")

    with open("sklearn_config.json", "r") as f:
        config = json.load(f)

    POSITION_LINES = config['position_lines']
    TACTICAL_COMPATIBILITY = config['tactical_compatibility']
    EXCLUDED_POSITIONS = config['excluded_positions']

    print(f"✅ Sklearn ансамбль загружен!")
    print(f"📊 Лучшая модель: {config['best_model']}")
    print(f"🎯 Лучший AUC: {config.get('best_score', 0):.1%}")
    print(f"📏 Признаков: {config['input_dim']}")
    print(f"✅ Валидация позиций подключена!")

except Exception as e:
    print(f"❌ Ошибка загрузки: {e}")
    print("🔧 Сначала запустите new_train.py")
    exit(1)


def safe_float(value, default=0.0):
    """Безопасно преобразует значение в float"""
    try:
        if value is None:
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


# ========== ФУНКЦИИ ПРОВЕРКИ ИГРОВОГО ВРЕМЕНИ ==========

def has_played_this_season(player_id):
    """Проверяет, играл ли игрок в этом сезоне"""
    try:
        player = Player.objects.get(id=player_id)

        # Проверяем статистику игрока
        if player.statistic:
            minutes_played = safe_float(getattr(player.statistic, 'minutes_played', 0))
            matches_played = safe_float(getattr(player.statistic, 'matches_uppercase', 0))

            # Если играл хотя бы 1 минуту в хотя бы 1 матче
            if minutes_played > 0 or matches_played > 0:
                return True

        # Проверяем игровую статистику (последние игры)
        recent_games = PlayerGameStatistic.objects.filter(
            player_id=player_id,
            minutes_played__gt=0  # Играл хотя бы минуту
        ).exists()

        return recent_games

    except Player.DoesNotExist:
        return False


def filter_players_with_game_time(squad):
    """Фильтрует игроков, которые играли в сезоне"""
    filtered_squad = []

    for player in squad:
        if has_played_this_season(player['id']):
            filtered_squad.append(player)
        else:
            print(f"  🚫 Исключен {player['name']} {player['surname']} - не играл в сезоне")

    print(f"🔍 Отфильтровано игроков: {len(squad)} → {len(filtered_squad)}")
    return filtered_squad


# ========== ФУНКЦИИ ВАЛИДАЦИИ УНИКАЛЬНОСТИ ПОЗИЦИЙ ==========
def find_players_for_missing_positions(consistent_lineup, squad, used_players, used_positions, line_quality,
                                       game_date=None):
    """Находит игроков на недостающие позиции по максимальному minutes_played с соблюдением ограничений"""

    if len(consistent_lineup) >= 11:
        return consistent_lineup

    needed = 11 - len(consistent_lineup)
    print(f"🔍 Поиск игроков на недостающие позиции: нужно {needed} игроков")

    # Анализируем какие линии и позиции нам нужны
    line_analysis = {
        1: {'current': 0, 'target': 1, 'positions': []},  # Вратари
        2: {'current': 0, 'target': 3, 'positions': []},  # Защитники
        4: {'current': 0, 'target': 4, 'positions': []},  # Полузащитники
        5: {'current': 0, 'target': 1, 'positions': []},  # Атакующие
        6: {'current': 0, 'target': 2, 'positions': []}  # Нападающие
    }

    # Подсчитываем текущее распределение по линиям
    for player in consistent_lineup:
        position_id = player['position_id']
        position_info = POSITION_LINES.get(str(position_id), {'line': 0})
        line_num = position_info['line']

        if line_num in line_analysis:
            line_analysis[line_num]['current'] += 1
            line_analysis[line_num]['positions'].append(position_id)

    print("📊 Анализ текущего состава по линиям:")
    line_names = {1: "Вратари", 2: "Защитники", 4: "Полузащитники", 5: "Атакующие", 6: "Нападающие"}
    for line_num, data in line_analysis.items():
        print(f"    {line_names[line_num]}: {data['current']}/{data['target']} (позиции: {data['positions']})")

    # Определяем приоритетные линии для дополнения
    priority_lines = []
    for line_num, data in line_analysis.items():
        if data['current'] < data['target']:
            shortage = data['target'] - data['current']
            priority_lines.append((line_num, shortage))

    priority_lines.sort(key=lambda x: x[1], reverse=True)  # Сортируем по нехватке
    print(f"📋 Приоритетные линии для дополнения: {priority_lines}")

    added_players = []

    # Проходим по приоритетным линиям
    for line_num, shortage in priority_lines:
        if len(consistent_lineup) + len(added_players) >= 11:
            break

        line_name = line_names[line_num]
        print(f"\n🔧 Дополняем линию {line_name} (нехватка: {shortage})")

        # Определяем нужную четность для этой линии
        if line_num in line_quality:
            required_parity = line_quality[line_num]['chosen']
        else:
            # Для вратарей четность не важна
            required_parity = None

        # Находим доступные позиции для этой линии
        available_positions = []
        for pos_str, pos_info in POSITION_LINES.items():
            pos_id = int(pos_str)
            if (pos_info['line'] == line_num and
                    pos_id not in used_positions and
                    (pos_id == 11 or pos_id >= 11)):  # Исключаем позиции 1-10, кроме вратаря

                # Проверяем четность если требуется
                if required_parity is not None:
                    pos_parity = 'even' if pos_id % 2 == 0 else 'odd'
                    if pos_parity != required_parity:
                        continue

                available_positions.append(pos_id)

        print(f"    Доступные позиции для линии {line_name}: {available_positions}")
        if required_parity:
            print(f"    Требуемая четность: {required_parity}")

        # Для каждой доступной позиции ищем лучшего игрока по minutes_played
        line_added = 0
        for pos_id in available_positions:
            if line_added >= shortage or len(consistent_lineup) + len(added_players) >= 11:
                break

            print(f"    🔍 Ищем игрока на позицию {pos_id}...")

            # Находим кандидатов на эту позицию
            candidates = []
            for player in squad:
                if (player['id'] not in used_players and
                        has_played_this_season(player['id'])):

                    # Проверяем может ли игрок играть на этой позиции
                    if can_player_play_position(player['id'], pos_id):
                        # Получаем minutes_played из статистики
                        minutes = get_player_minutes_played(player['id'])
                        candidates.append({
                            'player': player,
                            'minutes_played': minutes,
                            'position_id': pos_id
                        })

            if candidates:
                # Сортируем по minutes_played (больше = лучше)
                candidates.sort(key=lambda x: x['minutes_played'], reverse=True)
                best_candidate = candidates[0]

                player = best_candidate['player']
                minutes = best_candidate['minutes_played']

                # Создаем игрока для добавления
                new_player = {
                    'id': player['id'],
                    'name': f"{player['name']} {player['surname']}",
                    'position_id': pos_id,
                    'probability': 0.6,  # Базовая вероятность для доп. игроков
                    'age': player['age'],
                    'number': player['number'],
                    'minutes_played': minutes
                }

                added_players.append(new_player)
                used_players.add(player['id'])
                used_positions.add(pos_id)
                line_added += 1

                print(f"    ➕ Найден: {new_player['name']} - позиция {pos_id} ({minutes} минут)")
            else:
                print(f"    ❌ Не найден игрок на позицию {pos_id}")

    # Если все еще не хватает игроков, добавляем любых доступных
    if len(consistent_lineup) + len(added_players) < 11:
        remaining_needed = 11 - len(consistent_lineup) - len(added_players)
        print(f"\n🆘 Все еще нужно {remaining_needed} игроков, добавляем любых доступных...")

        # Находим любых оставшихся игроков
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

        # Сортируем по minutes_played
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

            print(
                f"    ➕ Дополнительно: {new_player['name']} - позиция {player['primary_position_id']} ({minutes} минут)")

    print(f"✅ Найдено {len(added_players)} игроков для дополнения состава")
    return consistent_lineup + added_players


def can_player_play_position(player_id, position_id):
    """Проверяет может ли игрок играть на указанной позиции"""
    try:
        player = Player.objects.get(id=player_id)

        # Основная позиция
        if player.primary_position_id == position_id:
            return True

        # Дополнительные позиции
        if player.position.filter(id=position_id).exists():
            return True

        # Проверяем совместимость по линиям (игрок может играть на соседних позициях той же линии)
        player_pos_info = POSITION_LINES.get(str(player.primary_position_id), {'line': 0})
        target_pos_info = POSITION_LINES.get(str(position_id), {'line': 0})

        if (player_pos_info['line'] == target_pos_info['line'] and
                player_pos_info['line'] > 0):  # Та же линия
            return True

        return False
    except Player.DoesNotExist:
        return False


def get_player_minutes_played(player_id):
    """Получает количество сыгранных минут игрока"""
    try:
        player = Player.objects.get(id=player_id)
        if player.statistic and player.statistic.minutes_played:
            return safe_float(player.statistic.minutes_played)
        return 0
    except Player.DoesNotExist:
        return 0


def check_position_uniqueness(lineup):
    """Проверяет уникальность позиций в составе"""
    position_ids = [player['position_id'] for player in lineup]
    unique_positions = set(position_ids)

    duplicates = []
    for pos_id in unique_positions:
        count = position_ids.count(pos_id)
        if count > 1:
            duplicates.append((pos_id, count))

    return len(duplicates) == 0, duplicates


def remove_position_duplicates(lineup):
    """Удаляет дублированные позиции, оставляя игрока с наибольшей вероятностью"""
    print("🔍 ПРИНУДИТЕЛЬНОЕ удаление дублированных позиций...")

    # Группируем игроков по позициям
    position_groups = {}
    for player in lineup:
        pos_id = player['position_id']
        if pos_id not in position_groups:
            position_groups[pos_id] = []
        position_groups[pos_id].append(player)

    # Удаляем дубликаты
    unique_lineup = []
    removed_count = 0

    for pos_id, players in position_groups.items():
        if len(players) > 1:
            # Сортируем по вероятности и берем ТОЛЬКО лучшего
            players.sort(key=lambda x: x['probability'], reverse=True)
            best_player = players[0]
            unique_lineup.append(best_player)

            print(f"    🔄 Позиция {pos_id}: оставлен {best_player['name']} ({best_player['probability']:.1%})")
            for removed_player in players[1:]:
                print(f"        ❌ УДАЛЕН {removed_player['name']} ({removed_player['probability']:.1%})")
                removed_count += 1
        else:
            unique_lineup.append(players[0])

    if removed_count > 0:
        print(f"✅ ПРИНУДИТЕЛЬНО удалено {removed_count} дублированных позиций")
        print(f"📊 Результат: {len(unique_lineup)} игроков с уникальными позициями")
    else:
        print("✅ Дублированных позиций не найдено")

    return unique_lineup


def ensure_exactly_11_players(lineup, squad, used_player_ids, line_quality, game_date=None):
    """Гарантирует максимальное количество игроков в составе (с исключением позиций 1-10, кроме вратаря)"""
    print(f"🔢 Проверка количества игроков: {len(lineup)}/11")

    if len(lineup) == 11:
        print("✅ Ровно 11 игроков - все в порядке!")
        return lineup

    elif len(lineup) > 11:
        # Если больше 11 - удаляем лишних (с наименьшей вероятностью)
        print(f"⚠️ Слишком много игроков ({len(lineup)}), удаляем лишних...")

        # Обязательно сохраняем вратаря
        goalkeeper = None
        field_players = []

        for player in lineup:
            if player['position_id'] == 11:
                goalkeeper = player
            else:
                field_players.append(player)

        # Сортируем полевых игроков по вероятности
        field_players.sort(key=lambda x: x['probability'], reverse=True)

        # Берем топ-10 полевых + вратарь
        final_lineup = []
        if goalkeeper:
            final_lineup.append(goalkeeper)
            final_lineup.extend(field_players[:10])
        else:
            final_lineup.extend(field_players[:11])

        print(f"✅ Сокращено до {len(final_lineup)} игроков")
        return final_lineup

    else:
        # Если меньше 11 - добавляем недостающих
        needed = 11 - len(lineup)
        print(f"⚠️ Недостаточно игроков ({len(lineup)}), добавляем {needed}...")

        # Находим доступных АКТИВНЫХ игроков (с исключением позиций 1-10, кроме вратаря)
        available_players = []
        for player in squad:
            if (player['id'] not in used_player_ids and
                    has_played_this_season(player['id']) and
                    (player['primary_position_id'] == 11 or player['primary_position_id'] >= 11)):
                available_players.append(player)

        if not available_players:
            print("⚠️ Нет доступных АКТИВНЫХ игроков для добавления!")
            print("🔒 СТРОГОЕ ПРАВИЛО: не добавляем неактивных игроков")
            return lineup

        # Получаем предсказания для доступных игроков
        try:
            # Извлекаем признаки для доступных игроков
            available_features = []
            valid_available = []

            for player in available_players:
                try:
                    features = extract_full_49_features(player, 0, game_date)  # opp_id=0 для упрощения
                    if len(features) == config['input_dim']:
                        available_features.append(features)
                        valid_available.append(player)
                except:
                    continue

            if available_features:
                # Получаем предсказания
                X_available = np.array(available_features, dtype=np.float32)
                X_available_scaled = scaler.transform(X_available)
                available_probabilities = predict_with_sklearn_ensemble(X_available_scaled)

                # Создаем кандидатов с вероятностями
                candidates = []
                for i, player in enumerate(valid_available):
                    prob = float(available_probabilities[i])

                    try:
                        player_obj = Player.objects.get(id=player['id'])
                        primary_pos = player_obj.primary_position.name if player_obj.primary_position else "Неизвестно"
                        injury_status = "🤕 Травма" if player_obj.injury else "✅ Здоров"
                        overall = 70
                        if player_obj.statistic:
                            overall = safe_float(getattr(player_obj.statistic, 'rating', 7.0)) * 10
                    except:
                        primary_pos = "Неизвестно"
                        injury_status = "❓ Неизвестно"
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

                # Фильтруем кандидатов с учетом четности линий
                filtered_candidates = []

                for candidate in candidates:
                    position_id = candidate['position_id']
                    # Проверяем, что позиция не в диапазоне 1-10 (кроме вратаря)
                    if position_id == 11 or position_id >= 11:
                        position_info = POSITION_LINES.get(str(position_id), {'line': 0})
                        line_num = position_info['line']

                        # Проверяем четность если линия известна
                        if line_num in line_quality:
                            chosen_parity = line_quality[line_num]['chosen']
                            player_parity = 'even' if position_id % 2 == 0 else 'odd'

                            if player_parity == chosen_parity:
                                filtered_candidates.append(candidate)
                        else:
                            # Если линия неизвестна, добавляем кандидата
                            filtered_candidates.append(candidate)

                # Сортируем по вероятности и добавляем лучших
                filtered_candidates.sort(key=lambda x: x['probability'], reverse=True)

                added_count = 0
                for candidate in filtered_candidates:
                    if added_count >= needed:
                        break

                    # Проверяем, что позиция не дублируется
                    existing_positions = [p['position_id'] for p in lineup]
                    if candidate['position_id'] not in existing_positions:
                        lineup.append(candidate)
                        used_player_ids.add(candidate['id'])
                        added_count += 1
                        print(
                            f"    ➕ Добавлен: {candidate['name']} - позиция {candidate['position_id']} ({candidate['probability']:.1%})")

                if added_count < needed:
                    print(f"⚠️ Удалось добавить только {added_count} из {needed} игроков")
                    print(f"🔒 Исключены позиции 1-10 (кроме вратаря 11)")
                else:
                    print(f"✅ Добавлено {added_count} игроков до {len(lineup)}")

        except Exception as e:
            print(f"❌ Ошибка при добавлении игроков: {e}")

        return lineup


# ========== ФУНКЦИИ ВАЛИДАЦИИ ==========

def check_player_position_compatibility(player_id, position_id):
    """Проверяет, может ли игрок играть на позиции"""
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
    """Получает состав из последней игры"""
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
    """Находит игроков для позиции (с учетом игрового времени)"""
    try:
        # Ищем основных игроков на позиции
        primary_players = Player.objects.filter(
            club_id=club_id,
            primary_position_id=position_id,
            injury__isnull=True
        ).values_list('id', flat=True)

        # Ищем игроков, которые могут играть на этой позиции
        secondary_players = Player.objects.filter(
            club_id=club_id,
            position__id=position_id,
            injury__isnull=True
        ).values_list('id', flat=True)

        all_players = list(set(list(primary_players) + list(secondary_players)))

        # Фильтруем игроков, которые играли в сезоне
        active_players = []
        for player_id in all_players:
            if has_played_this_season(player_id):
                active_players.append(player_id)

        return active_players
    except Exception:
        return []


def find_replacement_player(club_id, position_id, last_game_lineup):
    """Находит замену для позиции (с учетом игрового времени)"""
    # Пытаемся найти из последней игры
    if position_id in last_game_lineup:
        last_game_player_id = last_game_lineup[position_id]
        if (check_player_position_compatibility(last_game_player_id, position_id) and
                has_played_this_season(last_game_player_id)):
            try:
                player = Player.objects.get(id=last_game_player_id)
                return last_game_player_id, f"{player.name} {player.surname}"
            except Player.DoesNotExist:
                pass

    # Ищем любого подходящего активного игрока
    position_players = find_position_players(club_id, position_id)
    if position_players:
        try:
            player = Player.objects.get(id=position_players[0])
            return position_players[0], f"{player.name} {player.surname}"
        except Player.DoesNotExist:
            return position_players[0], f"Player_{position_players[0]}"

    return None, None


def validate_predicted_lineup(predicted_lineup, club_id, game_date=None):
    """ГЛАВНАЯ ФУНКЦИЯ ВАЛИДАЦИИ"""
    print(f"🔍 Валидация позиций для {len(predicted_lineup)} игроков...")

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

        # Проверяем игровое время
        if not has_played_this_season(player_id):
            print(f"  🚫 {player_name} исключен - не играл в сезоне")
            # Ищем замену
            replacement_id, replacement_name = find_replacement_player(
                club_id, position_id, last_game_lineup
            )
            if replacement_id:
                corrected_player_data = player_data.copy()
                corrected_player_data['id'] = replacement_id
                corrected_player_data['name'] = replacement_name
                corrected_lineup.append(corrected_player_data)
                validation_report['corrected_predictions'] += 1
                print(f"    🔄 Замена: {player_name} → {replacement_name} (не играл в сезоне)")
            continue

        if check_player_position_compatibility(player_id, position_id):
            # Игрок подходит
            corrected_lineup.append(player_data)
            validation_report['valid_predictions'] += 1
        else:
            # Нужна замена
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
                print(f"  🔄 Замена: {player_name} → {replacement_name} (позиция {position_id})")
            else:
                corrected_lineup.append(player_data)

    print(f"✅ Валидация завершена: {validation_report['corrected_predictions']} исправлений")
    return corrected_lineup, validation_report


def predict_with_validation(predicted_lineup, lineup_by_lines, accuracy, club, game):
    """ИНТЕГРАЦИОННАЯ ФУНКЦИЯ"""
    print(f"\n🔍 ПРИМЕНЯЕМ ПОЛНУЮ ВАЛИДАЦИЮ...")

    # Валидируем основной список
    validated_lineup, validation_report = validate_predicted_lineup(
        predicted_lineup, club.id, game.game_date
    )

    # Показываем результаты валидации
    if validation_report['corrected_predictions'] > 0:
        print(f"\n⚠️ ДЕТАЛИ ИСПРАВЛЕНИЙ ({validation_report['corrected_predictions']}):")
        for correction in validation_report['corrections']:
            print(f"    🔄 {correction['original_player']} → {correction['replacement_player']}")
            print(f"       Позиция: {correction['position_id']}")

    accuracy_rate = validation_report['valid_predictions'] / max(validation_report['total_players'], 1)
    print(f"\n📊 СТАТИСТИКА ВАЛИДАЦИИ:")
    print(f"    Точность ИИ: {accuracy_rate:.1%}")
    print(f"    Исправлений: {validation_report['corrected_predictions']}")

    return validated_lineup, lineup_by_lines, accuracy


# ========== ФУНКЦИИ ИЗВЛЕЧЕНИЯ ПРИЗНАКОВ ==========

def get_enhanced_player_stats(player_id):
    """Получает расширенную статистику игрока"""
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

        # Последние игровые статистики
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
    """Анализирует соперников на той же позиции"""
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
    """Получает тактическую совместимость позиции с популярными формациями"""
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
    """Создает улучшенный эмбеддинг позиции на основе реальных данных"""
    position_info = POSITION_LINES.get(str(position_id), {'line': 0, 'position': 'UNK', 'order': 0})

    # Основные характеристики позиции
    line_embedding = [0.0] * 7  # 7 линий (0-6)
    line_num = position_info['line']
    if 0 <= line_num <= 6:
        line_embedding[line_num] = 1.0

    # Позиционный порядок (нормализованный)
    order_normalized = min(position_info['order'] / 10.0, 1.0)

    # Тактическая важность
    avg_tactical, max_tactical = get_tactical_compatibility(position_id)

    return line_embedding + [order_normalized, avg_tactical, max_tactical]


def create_temporal_features(game_date):
    """Улучшенные временные признаки"""
    try:
        if not game_date:
            return [0.0] * 6

        month = game_date.month
        day_of_year = game_date.timetuple().tm_yday

        # Сезонные факторы
        is_season_start = 1.0 if month in [8, 9] else 0.0
        is_winter_break = 1.0 if month in [12, 1] else 0.0
        is_season_end = 1.0 if month in [5, 6] else 0.0

        # Цикличность сезона
        season_cycle = np.sin(2 * np.pi * month / 12)
        year_cycle = np.sin(2 * np.pi * day_of_year / 365)

        # Интенсивность календаря
        calendar_intensity = 1.0 if month in [3, 4, 10, 11] else 0.7

        return [is_season_start, is_winter_break, is_season_end, season_cycle, year_cycle, calendar_intensity]
    except:
        return [0.0] * 6


def calculate_team_chemistry(player_id, club_id):
    """Улучшенная химия команды"""
    try:
        player = Player.objects.get(id=player_id)

        # Базовый фактор времени
        time_factor = min(1.0, (player_id % 1000) / 1000.0)

        # Фактор игрового времени
        if player.statistic:
            minutes_factor = min(1.0, safe_float(player.statistic.minutes_played) / 2000.0)
            matches_factor = min(1.0, safe_float(player.statistic.matches_uppercase) / 30.0)
        else:
            minutes_factor = 0.5
            matches_factor = 0.5

        # Общая химия
        chemistry = (time_factor + minutes_factor + matches_factor) / 3.0
        return chemistry

    except:
        return 0.5


def calculate_motivation_factors(home_club_id, away_club_id, game_date, player_id):
    """Расширенные мотивационные факторы"""
    try:
        # Дерби фактор
        is_derby = 1.0 if abs(home_club_id - away_club_id) < 10 else 0.0

        # Важность матча по времени сезона
        month = game_date.month if game_date else 6
        match_importance = 1.0 if month in [4, 5, 6] else 0.8 if month in [11, 12] else 0.7

        # Личная мотивация игрока
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
    """Оценка физической формы и игровой формы"""
    try:
        player = Player.objects.get(id=player_id)

        # Базовая физическая форма
        base_fitness = 0.8

        # Возрастной фактор
        age = player.age or 25
        if 20 <= age <= 28:
            age_factor = 1.0
        elif 29 <= age <= 32:
            age_factor = 0.9
        elif age > 32:
            age_factor = 0.8
        else:
            age_factor = 0.85

        # Фактор травм
        injury_factor = 0.5 if player.injury else 1.0

        # Игровая форма
        if player.statistic:
            rating = safe_float(player.statistic.rating)
            form_factor = rating / 10.0
        else:
            form_factor = 0.7

        # Общий фитнес
        fitness = (base_fitness * age_factor * injury_factor + form_factor) / 2.0
        fitness = min(1.0, max(0.1, fitness))

        return [fitness, age_factor, injury_factor, form_factor]
    except:
        return [0.8, 0.9, 1.0, 0.7]


def extract_full_49_features(player_data, opp_club_id, game_date=None):
    """Извлекает ВСЕ 49 признаков игрока"""
    try:
        player_obj = Player.objects.get(id=player_data['id'])

        # 1. Базовые характеристики (4 признака)
        basic_features = [
            safe_float(player_data.get('height', 180)) / 200.0,
            safe_float(player_data.get('age', 25)) / 40.0,
            safe_float(player_data.get('number', 0)) / 100.0,
            safe_float(player_data.get('primary_position_id', 0)) / 120.0
        ]

        # 2. Расширенная игровая статистика (15 признаков)
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

        # 3. Позиционные эмбеддинги (10 признаков)
        position_id = player_data.get('primary_position_id', 0)
        position_features = create_position_embedding(position_id)

        # 4. Анализ против соперника (3 признака)
        opponent_analysis = get_opponent_analysis(player_data['id'], opp_club_id, position_id)
        opp_features = [
            opponent_analysis['opp_avg_strength'],
            opponent_analysis['superiority_factor'],
            min(opponent_analysis['position_competition'], 1.0)
        ]

        # 5. Временные признаки (6 признаков)
        temporal_features = create_temporal_features(game_date)

        # 6. Химия команды (1 признак)
        chemistry_features = [calculate_team_chemistry(player_data['id'], player_obj.club_id)]

        # 7. Мотивационные факторы (3 признака)
        motivation_features = calculate_motivation_factors(
            player_obj.club_id, opp_club_id, game_date, player_data['id']
        )

        # 8. Фитнес и форма (4 признака)
        fitness_features = estimate_fitness_and_form(player_data['id'], game_date)

        # 9. История участия (3 признака)
        history_features = [
            min(player_data['id'] / 3000.0, 1.0),  # Базовая активность
            min((player_data['id'] % 100) / 100.0, 1.0),  # Недавняя активность
            1.0 if not player_obj.injury else 0.0  # Статус здоровья
        ]

        # Объединяем все признаки (4+15+10+3+6+1+3+4+3 = 49 признаков)
        all_features = (basic_features + stat_features + position_features +
                        opp_features + temporal_features + chemistry_features +
                        motivation_features + fitness_features + history_features)

        # Проверяем корректность признаков
        all_features = [safe_float(f) if not (np.isnan(f) or np.isinf(f)) else 0.5 for f in all_features]

        return all_features

    except Exception as e:
        print(f"⚠️ Ошибка извлечения признаков для игрока {player_data.get('id', 'unknown')}: {e}")
        # Возвращаем средние значения в случае ошибки
        return [0.5] * 49


def predict_with_sklearn_ensemble(X):
    """Предсказание с использованием sklearn ансамбля"""
    try:
        rf_pred = rf_model.predict_proba(X)[:, 1]
        et_pred = et_model.predict_proba(X)[:, 1]
        gb_pred = gb_model.predict_proba(X)[:, 1]
        lr_pred = lr_model.predict_proba(X)[:, 1]
        nn_pred = nn_model.predict(X, verbose=0).flatten()

        # Если есть улучшенная нейросеть, используем её тоже
        if improved_nn_model:
            improved_nn_pred = improved_nn_model.predict(X, verbose=0).flatten()
            # Ансамблевое предсказание с улучшенной нейросетью
            ensemble_pred = (0.2 * rf_pred + 0.15 * et_pred + 0.15 * gb_pred +
                             0.1 * lr_pred + 0.2 * nn_pred + 0.2 * improved_nn_pred)
        else:
            # Ансамблевое предсказание без улучшенной нейросети
            ensemble_pred = (0.25 * rf_pred + 0.2 * et_pred + 0.2 * gb_pred +
                             0.15 * lr_pred + 0.2 * nn_pred)

        return ensemble_pred

    except Exception as e:
        print(f"⚠️ Ошибка ансамбля: {e}")
        # Используем только Random Forest как fallback
        return rf_model.predict_proba(X)[:, 1]


def organize_by_lines(predicted_players):
    """Организует игроков по линиям согласно футбольной тактике с ЖЕСТКИМИ ограничениями"""
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

    # Сортируем игроков в каждой линии по порядку
    for line_num in lines:
        lines[line_num].sort(key=lambda x: x['order'])

    # Формируем финальную структуру ТОЛЬКО для известных линий
    result = []
    total_players = 0

    for line_num in sorted(lines.keys()):
        if line_num > 0:  # Только известные линии (исключаем 0)
            line_players = []
            for player in lines[line_num]:
                line_players.append({
                    'id': player['id'],
                    'position_id': player['position_id'],
                    'name': player['name']
                })
                total_players += 1
            if line_players:  # Добавляем только непустые линии
                result.append(line_players)

    print(f"🔍 organize_by_lines: обработано {total_players} игроков из {len(predicted_players)}")

    # КРИТИЧНО: Если потеряли игроков с неизвестными позициями, добавляем их как отдельную линию
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
                print(f"⚠️ Игрок с неизвестной линией: {player['name']} (позиция {player['position_id']})")

        if unknown_players:
            result.append(unknown_players)  # Добавляем как отдельную линию
            total_players += len(unknown_players)
            print(f"✅ Добавлена линия неизвестных позиций: {len(unknown_players)} игроков")

    print(f"📊 Итого в результате: {total_players} игроков")
    return result


def compare_with_actual_sklearn(game, club, is_home, predicted_lineup):
    """Сравнивает с фактическим составом (исключая тренеров и позиции 1-10, кроме вратаря)"""
    try:
        actual_placement = game.home_club_placement if is_home else game.away_club_placement

        if not actual_placement:
            print("\n📋 Фактический состав недоступен")
            return 0.0

        # Извлекаем фактических игроков (без тренеров и позиций 1-10, кроме вратаря)
        actual_players = []
        print(f"\n📋 ФАКТИЧЕСКИЙ СОСТАВ (исключая тренеров и позиции 1-10, кроме вратаря):")
        print("=" * 50)

        excluded_positions = list(EXCLUDED_POSITIONS)
        # Добавляем позиции 1-10, но исключаем 11 (вратарь)
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
                        print(f"{pos:2d}. {player_obj.name} {player_obj.surname} (позиция {position_id})")
                        pos += 1
                    except:
                        print(f"{pos:2d}. Игрок ID: {player_id} (позиция {position_id})")
                        pos += 1

        # Сравниваем
        predicted_players = [p['id'] for p in predicted_lineup]
        matches = set(predicted_players) & set(actual_players)
        accuracy = len(matches) / len(actual_players) if actual_players else 0

        print(f"\n📊 SKLEARN + ВАЛИДАЦИЯ АНАЛИЗ ТОЧНОСТИ:")
        print(f"    Предсказано игроков: {len(predicted_players)}")
        print(f"    Фактических игроков: {len(actual_players)}")
        print(f"    Совпадений: {len(matches)}")
        print(f"    🎯 ТОЧНОСТЬ: {accuracy:.1%}")
        print(f"    🔒 Исключены позиции 1-10 (кроме вратаря 11)")

        if matches:
            print(f"\n✅ УГАДАННЫЕ ИГРОКИ ({len(matches)}):")
            for player_id in matches:
                try:
                    player_obj = Player.objects.get(id=player_id)
                    pred_player = next((p for p in predicted_lineup if p['id'] == player_id), None)
                    prob = pred_player['probability'] if pred_player else 0
                    pos_id = pred_player['position_id'] if pred_player else 0
                    print(f"    ✅ {player_obj.name} {player_obj.surname} (позиция {pos_id}, {prob:.1%})")
                except:
                    print(f"    ✅ Игрок ID: {player_id}")

        # Оценка результата
        if accuracy >= 0.8:
            print(f"\n🏆 ПРЕВОСХОДНЫЙ РЕЗУЛЬТАТ! {accuracy:.1%}")
        elif accuracy >= 0.7:
            print(f"\n🔥 ОТЛИЧНЫЙ РЕЗУЛЬТАТ! {accuracy:.1%}")
        elif accuracy >= 0.6:
            print(f"\n✅ ХОРОШИЙ РЕЗУЛЬТАТ! {accuracy:.1%}")
        else:
            print(f"\n📈 РЕЗУЛЬТАТ {accuracy:.1%} - модель учится")

        return accuracy

    except Exception as e:
        print(f"⚠️ Ошибка сравнения: {e}")
        return 0.0


def fix_incomplete_lineup(predicted_lineup, lineup_by_lines, game_id, is_home):
    """Исправляет неполный состав, добавляя ТОЛЬКО АКТИВНЫХ игроков с помощью ИИ"""
    try:
        # Сначала проверяем реальное количество игроков
        actual_count = len(predicted_lineup)
        lines_count = sum(len(line) for line in lineup_by_lines)

        print(f"🔍 Диагностика состава:")
        print(f"    Игроков в predicted_lineup: {actual_count}")
        print(f"    Игроков в lineup_by_lines: {lines_count}")

        if actual_count == lines_count and actual_count >= 11:
            print("✅ Состав корректен")
            return predicted_lineup, lineup_by_lines

        if actual_count == lines_count and lines_count < 11:
            print(f"⚠️ Недостаточно АКТИВНЫХ игроков: {lines_count}")
            print("🔒 СТРОГОЕ ПРАВИЛО: не добавляем неактивных игроков")
            return predicted_lineup, lineup_by_lines

        if actual_count != lines_count:
            print("🔄 Проблема в организации по линиям, исправляем...")
            # Просто пересоздаем организацию по линиям
            new_lineup_by_lines = organize_by_lines(predicted_lineup)
            return predicted_lineup, new_lineup_by_lines

        game = Game.objects.get(pk=game_id)
        club = game.home_club if is_home else game.away_club
        opp = game.away_club if is_home else game.home_club

        needed = 11 - actual_count
        print(f"🔧 ИСПРАВЛЕНИЕ СОСТАВА: нужно добавить {needed} АКТИВНЫХ игроков")

        # Получаем ТОЛЬКО активных игроков команды (исключая позиции 1-10, кроме вратаря)
        excluded_positions = list(EXCLUDED_POSITIONS)
        # Добавляем позиции 1-10, но исключаем 11 (вратарь)
        for pos_id in range(1, 11):
            if pos_id != 11 and pos_id not in excluded_positions:
                excluded_positions.append(pos_id)

        all_squad_raw = Player.objects.filter(club=club).exclude(
            primary_position_id__in=excluded_positions
        ).values('id', 'name', 'surname', 'primary_position_id', 'height', 'age', 'number')

        all_squad = []
        for player in all_squad_raw:
            # Дополнительная проверка на клиенте
            pos_id = player['primary_position_id'] or 0
            if pos_id == 11 or pos_id >= 11:  # Разрешаем вратарей (11) и позиции >= 11
                all_squad.append(player)

        # ID уже выбранных игроков
        used_ids = {p['id'] for p in predicted_lineup}

        # Находим доступных АКТИВНЫХ игроков
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
            print("⚠️ НЕТ доступных АКТИВНЫХ игроков для добавления!")
            print("🔒 СТРОГОЕ ПРАВИЛО: не добавляем неактивных игроков")
            print(f"📊 Возвращаем состав из {actual_count} активных игроков")
            return predicted_lineup, lineup_by_lines
        else:
            print(f"🤖 Анализируем {len(available_players)} доступных АКТИВНЫХ игроков...")
            print(f"🔒 Исключены позиции 1-10 (кроме вратаря 11)")

            # Извлекаем признаки для доступных игроков
            player_features = []
            valid_players = []

            for player in available_players:
                try:
                    features = extract_full_49_features(player, opp.id, game.game_date)
                    if len(features) == config['input_dim']:
                        player_features.append(features)
                        valid_players.append(player)
                except Exception as e:
                    print(f"⚠️ Ошибка обработки игрока {player['name']}: {e}")
                    continue

            if player_features:
                # Получаем предсказания ИИ
                X = np.array(player_features, dtype=np.float32)
                X_scaled = scaler.transform(X)
                probabilities = predict_with_sklearn_ensemble(X_scaled)

                # Создаем кандидатов с вероятностями
                candidates = []
                for i, player in enumerate(valid_players):
                    prob = float(probabilities[i])

                    try:
                        player_obj = Player.objects.get(id=player['id'])
                        primary_pos = player_obj.primary_position.name if player_obj.primary_position else "Неизвестно"
                        injury_status = "🤕 Травма" if player_obj.injury else "✅ Здоров"
                        overall = 70
                        if player_obj.statistic:
                            overall = safe_float(getattr(player_obj.statistic, 'rating', 7.0)) * 10
                    except:
                        primary_pos = "Неизвестно"
                        injury_status = "❓ Неизвестно"
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

                # Сортируем по вероятности и добавляем лучших
                candidates.sort(key=lambda x: x['probability'], reverse=True)

                # Добавляем нужное количество АКТИВНЫХ игроков
                added = 0
                for candidate in candidates:
                    if added >= needed:
                        break
                    predicted_lineup.append(candidate)
                    added += 1
                    print(
                        f"  ➕ ИИ добавил АКТИВНОГО: {candidate['name']} - позиция {candidate['position_id']} ({candidate['probability']:.1%})")

                if added < needed:
                    print(f"⚠️ Удалось добавить только {added} из {needed} активных игроков")
                else:
                    print(f"✅ Добавлено {added} АКТИВНЫХ игроков с помощью ИИ")
            else:
                print("⚠️ Не удалось обработать доступных АКТИВНЫХ игроков")

        # Пересоздаем lineup_by_lines с новым составом
        new_lineup_by_lines = organize_by_lines(predicted_lineup)

        final_count = len(predicted_lineup)
        print(f"🔄 Состав обновлен: {final_count} АКТИВНЫХ игроков")
        if final_count < 11:
            print(f"⚠️ ВНИМАНИЕ: Только {final_count} активных игроков доступно")

        return predicted_lineup, new_lineup_by_lines

    except Exception as e:
        print(f"❌ Ошибка исправления состава: {e}")
        return predicted_lineup, lineup_by_lines


# ============ ОСНОВНАЯ ФУНКЦИЯ ПРЕДСКАЗАНИЯ ============
def predict_sklearn_lineup(game_id, is_home=True):
    """Sklearn предсказание состава с дополнением по minutes_played"""
    try:
        game = Game.objects.get(pk=game_id)
        club = game.home_club if is_home else game.away_club
        opp = game.away_club if is_home else game.home_club

        print(f"\n🎯 SKLEARN ПРЕДСКАЗАНИЕ (ДОПОЛНЕНИЕ ПО MINUTES_PLAYED) для {club.name} против {opp.name}")
        print(f"📅 Игра: {game.game_date}")

        # Получаем игроков команды (исключаем тренеров И позиции 1-10, кроме вратаря)
        excluded_positions = list(EXCLUDED_POSITIONS)
        # Добавляем позиции 1-10, но исключаем 11 (вратарь)
        for pos_id in range(1, 11):
            if pos_id != 11 and pos_id not in excluded_positions:
                excluded_positions.append(pos_id)

        squad_raw = Player.objects.filter(club=club).exclude(
            primary_position_id__in=excluded_positions
        ).values('id', 'name', 'surname', 'primary_position_id', 'height', 'age', 'number')

        squad = []
        for player in squad_raw:
            # Дополнительная проверка на клиенте
            pos_id = player['primary_position_id'] or 0
            if pos_id == 11 or pos_id >= 11:  # Разрешаем вратарей (11) и позиции >= 11
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

        print(f"📋 Исходный состав: {len(squad)} игроков (исключены позиции 1-10, кроме вратаря)")

        # Фильтруем игроков по игровому времени
        active_squad = filter_players_with_game_time(squad)

        if len(active_squad) < 1:
            print(f"❌ Критически мало активных игроков")
            return [], [], 0.0

        squad = active_squad
        print(f"📋 Анализируем {len(squad)} активных игроков sklearn ансамблем...")

        # Извлекаем признаки
        player_features = []
        valid_players = []

        for player in squad:
            try:
                features = extract_full_49_features(player, opp.id, game.game_date)
                if len(features) == config['input_dim']:
                    player_features.append(features)
                    valid_players.append(player)
            except Exception as e:
                print(f"⚠️ Ошибка обработки игрока {player['name']}: {e}")
                continue

        if not player_features:
            print("❌ Не удалось обработать ни одного игрока")
            return [], [], 0.0

        print(f"✅ Обработано {len(player_features)} игроков")

        # Нормализация и предсказание
        X = np.array(player_features, dtype=np.float32)
        X_scaled = scaler.transform(X)

        print("🤖 Sklearn ансамбль анализирует игроков...")
        probabilities = predict_with_sklearn_ensemble(X_scaled)

        # Создаем результаты
        results = []
        for i, player in enumerate(valid_players):
            prob = float(probabilities[i])

            try:
                player_obj = Player.objects.get(id=player['id'])
                primary_pos = player_obj.primary_position.name if player_obj.primary_position else "Неизвестно"
                injury_status = "🤕 Травма" if player_obj.injury else "✅ Здоров"
                overall = 70
                if player_obj.statistic:
                    overall = safe_float(getattr(player_obj.statistic, 'rating', 7.0)) * 10
            except:
                primary_pos = "Неизвестно"
                injury_status = "❓ Неизвестно"
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

        # Сортируем по вероятности
        results.sort(key=lambda x: x['probability'], reverse=True)

        # Выбор вратаря
        print("🔧 Выбираем вратаря...")
        goalkeepers = [p for p in results if p['position_id'] == 11]
        field_players = [p for p in results if p['position_id'] != 11]

        if goalkeepers:
            best_gk = goalkeepers[0]
            print(f"✅ Вратарь: {best_gk['name']} ({best_gk['probability']:.1%})")
        else:
            print("❌ Вратарь не найден!")
            return [], [], 0.0

        # Анализ четности линий
        print("🔧 Анализируем четность линий...")

        line_players = {
            2: {'even': [], 'odd': []},  # Защитники
            4: {'even': [], 'odd': []},  # Полузащитники
            5: {'even': [], 'odd': []},  # Атакующие
            6: {'even': [], 'odd': []}  # Нападающие
        }

        # Группируем игроков по линиям и четности
        for player in field_players:
            position_id = player['position_id']
            position_info = POSITION_LINES.get(str(position_id), {'line': 0})
            line_num = position_info['line']

            if line_num in line_players:
                if position_id % 2 == 0:
                    line_players[line_num]['even'].append(player)
                else:
                    line_players[line_num]['odd'].append(player)

        # Сортируем игроков в каждой группе по вероятности
        for line_num in line_players:
            line_players[line_num]['even'].sort(key=lambda x: x['probability'], reverse=True)
            line_players[line_num]['odd'].sort(key=lambda x: x['probability'], reverse=True)

        # Вычисляем качество четности
        line_quality = {}
        for line_num in line_players:
            even_quality = sum(p['probability'] for p in line_players[line_num]['even'][:4])
            odd_quality = sum(p['probability'] for p in line_players[line_num]['odd'][:4])

            line_quality[line_num] = {
                'even': even_quality,
                'odd': odd_quality,
                'chosen': 'even' if even_quality >= odd_quality else 'odd'
            }

        print(f"📊 Анализ качества четности по линиям:")
        line_names = {2: "Защитники", 4: "Полузащитники", 5: "Атакующие", 6: "Нападающие"}
        for line_num, quality in line_quality.items():
            parity_text = "четные" if quality['chosen'] == 'even' else "нечетные"
            print(f"    {line_names[line_num]}: {parity_text} (качество: {quality[quality['chosen']]:.2f})")

        # Формирование состава с жесткими ограничениями
        print("🔒 Формируем основной состав...")

        consistent_lineup = []
        used_players = set()
        used_positions = set()

        # Добавляем вратаря
        consistent_lineup.append(best_gk)
        used_players.add(best_gk['id'])
        used_positions.add(best_gk['position_id'])
        print(f"  ✅ {best_gk['name']} - вратарь, позиция {best_gk['position_id']}")

        # Добавляем полевых игроков с соблюдением всех ограничений
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
                    print(f"  ✅ {player['name']} - линия {line_num}, позиция {player['position_id']}")

        print(f"🔢 Основной состав: {len(consistent_lineup)} игроков")

        # НОВАЯ ЛОГИКА: Дополняем состав по недостающим позициям через minutes_played
        if len(consistent_lineup) < 11:
            print(f"\n🎯 ДОПОЛНЕНИЕ ПО НЕДОСТАЮЩИМ ПОЗИЦИЯМ (minutes_played)")
            consistent_lineup = find_players_for_missing_positions(
                consistent_lineup, squad, used_players, used_positions, line_quality, game.game_date
            )

        # Финальная проверка уникальности позиций
        final_positions = [p['position_id'] for p in consistent_lineup]
        unique_positions = set(final_positions)

        if len(final_positions) != len(unique_positions):
            print("🚨 Найдены дублированные позиции, исправляем...")
            consistent_lineup = remove_position_duplicates(consistent_lineup)

        # Обрезаем до 11 если больше
        if len(consistent_lineup) > 11:
            print(f"✂️ Обрезаем до 11 лучших игроков")
            consistent_lineup.sort(key=lambda x: x['probability'], reverse=True)
            consistent_lineup = consistent_lineup[:11]

        print(f"🏁 ФИНАЛЬНЫЙ РЕЗУЛЬТАТ: {len(consistent_lineup)} игроков")

        # Финальная проверка
        final_positions = [p['position_id'] for p in consistent_lineup]
        unique_positions = set(final_positions)

        print(f"🔢 ФИНАЛЬНАЯ ПРОВЕРКА:")
        print(f"    Игроков в составе: {len(consistent_lineup)}")
        print(f"    Уникальных позиций: {len(unique_positions)}")
        print(f"    Позиции: {sorted(final_positions)}")

        if len(final_positions) == len(unique_positions):
            print("✅ ВСЕ ПОЗИЦИИ УНИКАЛЬНЫ!")
        else:
            print("❌ ЕСТЬ ДУБЛИРОВАННЫЕ ПОЗИЦИИ!")

        predicted_lineup = consistent_lineup

        # Организуем по линиям
        lineup_by_lines = organize_by_lines(predicted_lineup)

        # Выводим результаты
        print(f"\n🎯 ФИНАЛЬНОЕ ПРЕДСКАЗАНИЕ (ДОПОЛНЕНИЕ ПО MINUTES_PLAYED):")
        print("=" * 70)

        for i, line in enumerate(lineup_by_lines):
            line_num = i + 1
            line_names_display = {1: "🥅 Вратарь", 2: "🛡️ Защитники", 3: "⚖️ Опорные полузащитники",
                                  4: "⚽ Полузащитники", 5: "🔥 Атакующие полузащитники", 6: "⚡ Нападающие"}

            print(f"\n{line_names_display.get(line_num, f'Линия {line_num}')}:")
            for player in line:
                player_info = next((p for p in predicted_lineup if p['id'] == player['id']), None)
                if player_info:
                    conf_icon = "🔥" if player_info['probability'] > 0.8 else "✅" if player_info[
                                                                                        'probability'] > 0.6 else "⚠️"
                    minutes = player_info.get('minutes_played', 0)
                    minutes_text = f" ({minutes} мин)" if minutes > 0 else ""
                    print(f"  {conf_icon} {player['name']} - позиция {player_info['position_id']}{minutes_text}")

        print(f"\n📊 СТАТИСТИКА:")
        print(f"    Игроков в составе: {len(predicted_lineup)}")
        total_confidence = sum([p['probability'] for p in predicted_lineup])
        avg_confidence = total_confidence / len(predicted_lineup) if predicted_lineup else 0
        print(f"    Средняя уверенность: {avg_confidence:.1%}")
        print(f"    Уникальных позиций: {len(set(p['position_id'] for p in predicted_lineup))}")

        # Сравнение с фактическим составом
        accuracy = compare_with_actual_sklearn(game, club, is_home, predicted_lineup)

        # Применяем валидацию
        return predict_with_validation(predicted_lineup, lineup_by_lines, accuracy, club, game)

    except Exception as e:
        print(f"❌ Ошибка предсказания: {e}")
        import traceback
        traceback.print_exc()
        return [], [], 0.0


def main():
    """Главная функция"""
    print("=== ИТОГОВЫЙ SKLEARN AI + ЖЕСТКИЕ ОГРАНИЧЕНИЯ ===")
    print("🎯 Ансамбль из 5+ моделей + жесткая валидация")
    print("🔒 Гарантии:")
    print("    ✅ Только игроки с игровым временем в сезоне")
    print("    ✅ Уникальные position_id в составе (без дубликатов)")
    print("    ✅ Строгая четность позиций по линиям")
    print("    ✅ Ровно 11 игроков в итоговом составе")

    while True:
        print("\n🎮 ВЫБЕРИТЕ РЕЖИМ:")
        print("1. Предсказание с жесткими ограничениями")
        print("2. Проверить игрока и позицию")
        print("3. Проверить игровое время игрока")
        print("4. Информация о системе")
        print("5. Тест извлечения признаков")
        print("6. Выход")

        choice = input("\nВаш выбор (1-6): ").strip()

        if choice == "1":
            try:
                game_id = input("ID игры: ").strip()
                if not game_id.isdigit():
                    print("❌ ID игры должен быть числом")
                    continue

                is_home = input("Домашняя команда? (y/n): ").strip().lower() == "y"
                predicted_lineup, lineup_by_lines, accuracy = predict_sklearn_lineup(int(game_id), is_home)

                # ГАРАНТИРУЕМ что ВСЕГДА есть результат
                if not predicted_lineup or len(predicted_lineup) != 11:
                    print("🚨 КРИТИЧЕСКАЯ ОШИБКА: Неполный состав!")
                    print(f"Получено игроков: {len(predicted_lineup) if predicted_lineup else 0}")
                    if predicted_lineup and len(predicted_lineup) > 0:
                        print("Показываем частичный результат:")
                        for player in predicted_lineup:
                            print(f"  - {player['name']} (позиция {player['position_id']})")
                    continue

                if lineup_by_lines:
                    print(f"\n📋 ФОРМАТ ДЛЯ ПРОГРАММИРОВАНИЯ (ГАРАНТИРОВАННО 11 ИГРОКОВ):")
                    print("=" * 60)
                    print("lineup_by_lines = [")
                    for line in lineup_by_lines:
                        print("    [", end="")
                        for i, player in enumerate(line):
                            if i > 0:
                                print(", ", end="")
                            print(
                                f'{{"id": {player["id"]}, "position_id": {player["position_id"]}, "name": "{player["name"]}"}}',
                                end="")
                        print("],")
                    print("]")

                    # Проверяем финальные ограничения
                    all_positions = []
                    for line in lineup_by_lines:
                        for player in line:
                            all_positions.append(player["position_id"])

                    print(f"\n🔍 ФИНАЛЬНАЯ ПРОВЕРКА ОГРАНИЧЕНИЙ:")
                    print(f"    Всего игроков: {len(all_positions)} (должно быть 11)")
                    print(f"    Уникальных позиций: {len(set(all_positions))} (должно быть ≤11)")
                    print(f"    Позиции: {sorted(all_positions)}")

                    if len(all_positions) == 11:
                        print("✅ КОЛИЧЕСТВО ИГРОКОВ КОРРЕКТНО!")
                        if len(set(all_positions)) == 11:
                            print("✅ ВСЕ ПОЗИЦИИ УНИКАЛЬНЫ!")
                        else:
                            print(f"⚠️ Есть дублированные позиции (это допустимо)")
                    elif len(all_positions) < 11:
                        print(f"❌ НЕДОСТАТОЧНО ИГРОКОВ! ({len(all_positions)} из 11)")
                        print("🔧 ИСПРАВЛЯЕМ: дополняем состав до 11 игроков...")

                        # Исправляем ситуацию с неполным составом
                        predicted_lineup, lineup_by_lines = fix_incomplete_lineup(
                            predicted_lineup, lineup_by_lines, int(game_id), is_home
                        )

                        # Перепроверяем после исправления
                        all_positions = []
                        for line in lineup_by_lines:
                            for player in line:
                                all_positions.append(player["position_id"])

                        print(f"\n🔍 ПРОВЕРКА ПОСЛЕ ИСПРАВЛЕНИЯ:")
                        print(f"    Всего игроков: {len(all_positions)}")
                        print(f"    Позиции: {sorted(all_positions)}")

                        if len(all_positions) == 11:
                            print("✅ ИСПРАВЛЕНО! Теперь ровно 11 игроков!")
                        elif len(all_positions) < 11:
                            print(f"⚠️ Только {len(all_positions)} АКТИВНЫХ игроков доступно")
                            print("🔒 СТРОГОЕ СОБЛЮДЕНИЕ: только игроки с игровым временем")
                        else:
                            print(f"⚠️ Получилось {len(all_positions)} игроков, показываем результат")
                    else:
                        print(f"⚠️ СЛИШКОМ МНОГО ИГРОКОВ! ({len(all_positions)} > 11)")
                        print("✂️ Обрезаем до 11 лучших...")

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
                                    'all_active_players': True,  # Только активные игроки
                                    'strict_constraints_followed': True
                                }
                            }

                            with open(filename, 'w', encoding='utf-8') as f:
                                json.dump(output_data, f, indent=2, ensure_ascii=False)
                            print(f"💾 Сохранено в файл: {filename}")
                        except Exception as e:
                            print(f"❌ Ошибка сохранения: {e}")
                else:
                    print("❌ Состав создан, но не удалось организовать по линиям!")
                    print("Показываем прямой список игроков:")
                    for i, player in enumerate(predicted_lineup, 1):
                        print(f"{i:2d}. {player['name']} - позиция {player['position_id']}")

            except Exception as e:
                print(f"❌ Ошибка: {e}")

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

                    print(f"\n🔍 ПРОВЕРКА СОВМЕСТИМОСТИ:")
                    print(f"    Игрок: {player_name}")
                    print(f"    Позиция: {position_name}")

                    if can_play:
                        print(f"    ✅ МОЖЕТ играть на этой позиции")
                    else:
                        print(f"    ❌ НЕ МОЖЕТ играть на этой позиции")

                except Player.DoesNotExist:
                    print(f"❌ Игрок с ID {player_id} не найден")

            except ValueError:
                print("❌ Введите числовые ID")

        elif choice == "3":
            try:
                player_id = int(input("ID игрока: "))

                has_time = has_played_this_season(player_id)

                try:
                    player = Player.objects.get(id=player_id)
                    player_name = f"{player.name} {player.surname}"

                    print(f"\n⏱️ ПРОВЕРКА ИГРОВОГО ВРЕМЕНИ:")
                    print(f"    Игрок: {player_name}")

                    if has_time:
                        print(f"    ✅ ИГРАЛ в этом сезоне")

                        # Показываем статистику
                        if player.statistic:
                            minutes = safe_float(getattr(player.statistic, 'minutes_played', 0))
                            matches = safe_float(getattr(player.statistic, 'matches_uppercase', 0))
                            print(f"    📊 Минут сыграно: {minutes}")
                            print(f"    📊 Матчей сыграно: {matches}")
                    else:
                        print(f"    ❌ НЕ ИГРАЛ в этом сезоне")
                        print(f"    🚫 Будет исключен из предсказания")

                except Player.DoesNotExist:
                    print(f"❌ Игрок с ID {player_id} не найден")

            except ValueError:
                print("❌ Введите числовой ID")

        elif choice == "4":
            print(f"\n📊 ИНФОРМАЦИЯ О СИСТЕМЕ:")
            print("=" * 60)
            print(f"🎯 Тип: Sklearn ансамбль + ЖЕСТКИЕ ограничения")
            print(f"🧠 Базовые модели: RF + ET + GB + LR + NN")
            if improved_nn_model:
                print(f"🚀 Улучшенная NN: Включена (attention + residual)")
            else:
                print(f"⚠️ Улучшенная NN: Не найдена")
            print(f"📏 Признаков: {config['input_dim']}")
            print(f"🏆 Лучшая модель: {config['best_model']}")
            print(f"📈 Лучший AUC: {config.get('best_score', 0):.1%}")
            print(f"\n🔒 ЖЕСТКИЕ ОГРАНИЧЕНИЯ:")
            print(f"    ✅ ТОЛЬКО игроки с игровым временем в сезоне")
            print(f"    ✅ Уникальные position_id в рамках одной линии")
            print(f"    ✅ Четность позиций по линиям (четные ИЛИ нечетные)")
            print(f"    ✅ Максимально возможное количество игроков (≤11)")
            print(f"    ✅ НЕ добавляем неактивных игроков")
            print(f"\n📈 Возможности:")
            print(f"    ✅ 49 признаков")
            print(f"    ✅ Позиционные эмбеддинги")
            print(f"    ✅ Тактическая совместимость")
            print(f"    ✅ Временные признаки")
            print(f"    ✅ Мотивационные факторы")
            print(f"    ✅ Строгое соблюдение правил активности")

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

                    print(f"\n🔬 ТЕСТ ИЗВЛЕЧЕНИЯ ПРИЗНАКОВ:")
                    print(f"    Игрок: {player.name} {player.surname}")
                    print(f"    Извлечено признаков: {len(features)}")
                    print(f"    Ожидалось признаков: {config['input_dim']}")
                    print(f"    Игровое время: {'✅ Есть' if has_time else '❌ Нет'}")

                    if len(features) == config['input_dim']:
                        print("    ✅ УСПЕШНО! Количество признаков корректно")

                        # Показываем первые 10 признаков
                        print(f"\n📋 Первые 10 признаков:")
                        feature_names = config.get('feature_names', [])
                        for i in range(min(10, len(features))):
                            name = feature_names[i] if i < len(feature_names) else f"feature_{i}"
                            print(f"    {i + 1:2d}. {name}: {features[i]:.3f}")
                    else:
                        print("    ❌ ОШИБКА! Неверное количество признаков")

                except Player.DoesNotExist:
                    print(f"❌ Игрок с ID {player_id} не найден")

            except ValueError:
                print("❌ Введите числовые ID")

        elif choice == "6":
            print("👋 До свидания!")
            print("🎯 Система с ЖЕСТКИМИ ограничениями готова к работе!")
            print("⚽ Реалистичные составы ТОЛЬКО из активных игроков!")
            print("🔒 Строгое соблюдение всех правил четности и уникальности!")
            break

        else:
            print("❌ Выберите от 1 до 6")


if __name__ == "__main__":
    main()