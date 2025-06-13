# ai_with_validation.py - Интегрированная версия ИИ с валидацией позиций

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

# Импортируем функции валидации
from position_validation import (
    validate_and_correct_predicted_lineup,
    validate_lineup_by_lines,
    check_player_position_compatibility,
    find_position_players_in_club,
    get_last_game_lineup
)

print("🎯 УЛУЧШЕННЫЙ SKLEARN AI С ВАЛИДАЦИЕЙ ПОЗИЦИЙ")
print("📊 Ансамбль: RF + ET + GB + LR + NN + Валидация позиций")

# Загружаем модели и конфигурацию
try:
    rf_model = joblib.load("sklearn_rf_model.pkl")
    et_model = joblib.load("sklearn_et_model.pkl")
    gb_model = joblib.load("sklearn_gb_model.pkl")
    lr_model = joblib.load("sklearn_lr_model.pkl")
    nn_model = load_model("sklearn_nn_model.keras", compile=False)
    scaler = joblib.load("sklearn_scaler.pkl")

    with open("sklearn_config.json", "r") as f:
        config = json.load(f)

    POSITION_LINES = config['position_lines']
    EXCLUDED_POSITIONS = config['excluded_positions']

    print(f"✅ Sklearn ансамбль загружен!")
    print(f"📊 Лучшая модель: {config['best_model']}")
    print(f"🎯 Точность: {config['best_accuracy']:.1%}")
    print(f"✅ Валидация позиций подключена!")

except Exception as e:
    print(f"❌ Ошибка загрузки: {e}")
    print("🔧 Сначала запустите sklearn_lineup_train.py")
    exit(1)


def safe_float(value, default=0.0):
    """Безопасно преобразует значение в float"""
    try:
        if value is None:
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


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

        # Последние игры
        recent_games = PlayerGameStatistic.objects.filter(
            player_id=player_id
        ).order_by('-game__game_date')[:5]

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


def extract_enhanced_features(player_data, opp_club_id):
    """Извлекает все 30 признаков игрока"""
    try:
        player_obj = Player.objects.get(id=player_data['id'])

        # 1. Базовые характеристики (4 признака)
        basic_features = [
            safe_float(player_data.get('height', 180)) / 200.0,
            safe_float(player_data.get('age', 25)) / 40.0,
            safe_float(player_data.get('number', 0)) / 100.0,
            safe_float(player_data.get('primary_position_id', 0)) / 120.0
        ]

        # 2. Расширенная статистика (15 признаков)
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

        # 3. Позиционные признаки (3 признака)
        position_id = safe_float(player_data.get('primary_position_id', 0))
        position_info = POSITION_LINES.get(str(int(position_id)), {'line': 0, 'position': 'Unknown', 'order': 0})

        position_features = [
            safe_float(position_info['line']) / 6.0,
            safe_float(position_info['order']) / 5.0,
            1.0 if str(int(position_id)) in POSITION_LINES else 0.0
        ]

        # 4. Анализ против соперника (3 признака)
        opponent_analysis = get_opponent_analysis(player_data['id'], opp_club_id, int(position_id))
        opp_features = [
            opponent_analysis['opp_avg_strength'],
            opponent_analysis['superiority_factor'],
            min(opponent_analysis['position_competition'], 1.0)
        ]

        # 5. История (3 признака)
        history_features = [
            min(player_data['id'] / 3000.0, 1.0),
            min((player_data['id'] % 100) / 100.0, 1.0),
            1.0 if not player_obj.injury else 0.0
        ]

        # 6. Стратегические признаки (2 признака)
        strategic_features = [
            0.8 if player_obj.age and 22 <= player_obj.age <= 29 else 0.6,
            1.0 if position_id == 11 else 0.9
        ]

        all_features = (basic_features + stat_features + position_features +
                        opp_features + history_features + strategic_features)

        # Проверяем корректность
        all_features = [safe_float(f) if not (np.isnan(f) or np.isinf(f)) else 0.5 for f in all_features]

        return all_features

    except Exception as e:
        # Возвращаем средние значения в случае ошибки
        return [0.5] * 30


def predict_with_sklearn_ensemble(X):
    """Предсказание с использованием sklearn ансамбля"""
    try:
        rf_pred = rf_model.predict_proba(X)[:, 1]
        et_pred = et_model.predict_proba(X)[:, 1]
        gb_pred = gb_model.predict_proba(X)[:, 1]
        lr_pred = lr_model.predict_proba(X)[:, 1]
        nn_pred = nn_model.predict(X, verbose=0).flatten()

        # Ансамблевое предсказание
        ensemble_pred = (0.25 * rf_pred + 0.25 * et_pred + 0.2 * gb_pred + 0.1 * lr_pred + 0.2 * nn_pred)
        return ensemble_pred

    except Exception as e:
        print(f"⚠️ Ошибка ансамбля: {e}")
        # Используем только Random Forest как fallback
        return rf_model.predict_proba(X)[:, 1]


def organize_by_lines(predicted_players):
    """Организует игроков по линиям согласно футбольной тактике"""
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
            'probability': player['probability'],
            'order': order
        })

    # Сортируем игроков в каждой линии по порядку (слева направо)
    for line_num in lines:
        lines[line_num].sort(key=lambda x: x['order'])

    # Формируем финальную структуру
    result = []
    for line_num in sorted(lines.keys()):
        if line_num > 0:  # Исключаем линию 0 (неизвестные позиции)
            line_players = []
            for player in lines[line_num]:
                line_players.append({
                    'id': player['id'],
                    'position_id': player['position_id'],
                    'name': player['name']
                })
            result.append(line_players)

    return result


def predict_sklearn_lineup_with_validation(game_id, is_home=True):
    """
    НОВАЯ ФУНКЦИЯ: Sklearn предсказание состава с валидацией позиций
    """
    try:
        game = Game.objects.get(pk=game_id)
        club = game.home_club if is_home else game.away_club
        opp = game.away_club if is_home else game.home_club

        print(f"\n🎯 SKLEARN + ВАЛИДАЦИЯ для {club.name} против {opp.name}")
        print(f"📅 Игра: {game.game_date}")

        # Получаем игроков команды (исключаем тренеров)
        squad_raw = Player.objects.filter(club=club).exclude(
            primary_position_id__in=EXCLUDED_POSITIONS
        ).values('id', 'name', 'surname', 'primary_position_id', 'height', 'age', 'number')

        squad = []
        for player in squad_raw:
            safe_player = {
                'id': player['id'],
                'name': player['name'] or 'Unknown',
                'surname': player['surname'] or 'Player',
                'primary_position_id': player['primary_position_id'] or 0,
                'height': player['height'] if player['height'] is not None else 180,
                'age': player['age'] if player['age'] is not None else 25,
                'number': player['number'] if player['number'] is not None else 0
            }
            squad.append(safe_player)

        if len(squad) < 11:
            print(f"❌ Недостаточно полевых игроков в команде: {len(squad)}")
            return [], [], 0.0, {}

        print(f"📋 Анализируем {len(squad)} полевых игроков sklearn ансамблем...")

        # Извлекаем признаки
        player_features = []
        valid_players = []

        for player in squad:
            try:
                features = extract_enhanced_features(player, opp.id)
                if len(features) == config['input_dim']:
                    player_features.append(features)
                    valid_players.append(player)
                else:
                    print(f"⚠️ Игрок {player['name']}: неверное количество признаков")
            except Exception as e:
                print(f"⚠️ Ошибка обработки игрока {player['name']}: {e}")
                continue

        if not player_features:
            print("❌ Не удалось обработать ни одного игрока")
            return [], [], 0.0, {}

        # Нормализация и предсказание
        X = np.array(player_features, dtype=np.float32)
        X_scaled = scaler.transform(X)

        print("🤖 Sklearn ансамбль анализирует игроков...")
        probabilities = predict_with_sklearn_ensemble(X_scaled)

        # Создаем результаты ДО валидации
        raw_results = []
        for i, player in enumerate(valid_players):
            prob = float(probabilities[i])

            # Дополнительная информация
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

            raw_results.append({
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

        # Сортируем по вероятности и берем топ-11
        raw_results.sort(key=lambda x: x['probability'], reverse=True)
        raw_predicted_lineup = raw_results[:11]

        print(f"\n🤖 БАЗОВОЕ ПРЕДСКАЗАНИЕ ИИ (ДО ВАЛИДАЦИИ):")
        print("=" * 60)
        for i, player in enumerate(raw_predicted_lineup, 1):
            conf_icon = "🔥" if player['probability'] > 0.8 else "✅" if player['probability'] > 0.6 else "⚠️"
            print(
                f"  {i:2d}. {conf_icon} {player['name']} (#{player['number']}) - {player['probability']:.1%} - {player['position_name']}")

        # ========== ПРИМЕНЯЕМ ВАЛИДАЦИЮ ПОЗИЦИЙ ==========
        print(f"\n🔍 ПРИМЕНЯЕМ ВАЛИДАЦИЮ ПОЗИЦИЙ...")
        print("=" * 60)

        # Подготавливаем данные для валидации
        validation_input = []
        for player in raw_predicted_lineup:
            validation_input.append({
                'id': player['id'],
                'position_id': player['position_id'],
                'name': player['name']
            })

        # Валидируем предсказание
        validated_lineup, validation_report = validate_and_correct_predicted_lineup(
            validation_input, club.id, game.game_date
        )

        # Обновляем информацию валидированных игроков
        final_predicted_lineup = []
        for validated_player in validated_lineup:
            # Ищем исходную информацию о игроке
            original_info = None
            for original in raw_predicted_lineup:
                if original['id'] == validated_player['id']:
                    original_info = original
                    break

            if original_info:
                # Игрок остался тот же
                final_predicted_lineup.append(original_info)
            else:
                # Игрок был заменен - получаем новую информацию
                try:
                    player_obj = Player.objects.get(id=validated_player['id'])
                    primary_pos = player_obj.primary_position.name if player_obj.primary_position else "Неизвестно"
                    injury_status = "🤕 Травма" if player_obj.injury else "✅ Здоров"
                    overall = 70
                    if player_obj.statistic:
                        overall = safe_float(getattr(player_obj.statistic, 'rating', 7.0)) * 10

                    final_predicted_lineup.append({
                        'id': validated_player['id'],
                        'name': validated_player['name'],
                        'position_id': validated_player['position_id'],
                        'position_name': primary_pos,
                        'probability': 0.7,  # Средняя вероятность для замененных игроков
                        'injury_status': injury_status,
                        'overall': overall,
                        'age': player_obj.age or 25,
                        'number': player_obj.number or 0
                    })
                except Player.DoesNotExist:
                    final_predicted_lineup.append({
                        'id': validated_player['id'],
                        'name': validated_player['name'],
                        'position_id': validated_player['position_id'],
                        'position_name': "Неизвестно",
                        'probability': 0.7,
                        'injury_status': "❓ Неизвестно",
                        'overall': 70,
                        'age': 25,
                        'number': 0
                    })

        # Организуем по линиям
        lineup_by_lines = organize_by_lines(final_predicted_lineup)

        # Выводим финальные результаты
        print(f"\n🎯 ФИНАЛЬНЫЙ СОСТАВ ПОСЛЕ ВАЛИДАЦИИ (TOP-11):")
        print("=" * 80)

        total_confidence = sum([p['probability'] for p in final_predicted_lineup])
        avg_confidence = total_confidence / 11

        line_names = {1: "🥅 Вратарь", 2: "🛡️ Защитники", 3: "⚖️ Опорные полузащитники",
                      4: "⚽ Полузащитники", 5: "🔥 Атакующие полузащитники", 6: "⚡ Нападающие"}

        for i, line in enumerate(lineup_by_lines):
            line_num = i + 1
            print(f"\n{line_names.get(line_num, f'Линия {line_num}')}:")
            for player in line:
                player_info = next((p for p in final_predicted_lineup if p['id'] == player['id']), None)
                if player_info:
                    conf_icon = "🔥" if player_info['probability'] > 0.8 else "✅" if player_info[
                                                                                        'probability'] > 0.6 else "⚠️"
                    print(
                        f"  {conf_icon} {player['name']} (#{player_info['number']}) - {player_info['probability']:.1%}")

        print(f"\n📊 СТАТИСТИКА ВАЛИДАЦИИ:")
        print(f"    Всего игроков: {validation_report['total_players']}")
        print(f"    Валидных предсказаний ИИ: {validation_report['valid_predictions']}")
        print(f"    Исправлений позиций: {validation_report['corrected_predictions']}")
        print(f"    Средняя уверенность: {avg_confidence:.1%}")

        if validation_report['issues']:
            print(f"\n⚠️ ДЕТАЛИ ИСПРАВЛЕНИЙ:")
            for issue in validation_report['issues']:
                if issue['type'] == 'position_mismatch_corrected':
                    original_player = next((p for p in raw_predicted_lineup if p['id'] == issue['original_player_id']),
                                           None)
                    original_name = original_player['name'] if original_player else f"ID:{issue['original_player_id']}"
                    corrected_player = next(
                        (p for p in final_predicted_lineup if p['id'] == issue['corrected_player_id']), None)
                    corrected_name = corrected_player[
                        'name'] if corrected_player else f"ID:{issue['corrected_player_id']}"
                    print(f"    🔄 {original_name} → {corrected_name} (позиция {issue['position_id']})")
                else:
                    print(f"    ⚠️ {issue['message']}")

        # Оценка качества
        if avg_confidence > 0.8:
            print("🏆 ОЧЕНЬ ВЫСОКАЯ УВЕРЕННОСТЬ!")
        elif avg_confidence > 0.7:
            print("🔥 ВЫСОКАЯ УВЕРЕННОСТЬ!")
        elif avg_confidence > 0.6:
            print("✅ ХОРОШАЯ УВЕРЕННОСТЬ!")
        else:
            print("⚠️ СРЕДНЯЯ УВЕРЕННОСТЬ.")

        # Сравнение с фактическим составом
        accuracy = compare_with_actual_sklearn(game, club, is_home, final_predicted_lineup)

        return final_predicted_lineup, lineup_by_lines, accuracy, validation_report

    except Exception as e:
        print(f"❌ Ошибка предсказания с валидацией: {e}")
        import traceback
        traceback.print_exc()
        return [], [], 0.0, {}


def compare_with_actual_sklearn(game, club, is_home, predicted_lineup):
    """Сравнивает с фактическим составом (исключая тренеров)"""
    try:
        actual_placement = game.home_club_placement if is_home else game.away_club_placement

        if not actual_placement:
            print("\n📋 Фактический состав недоступен")
            return 0.0

        # Извлекаем фактических игроков (без тренеров)
        actual_players = []
        print(f"\n📋 ФАКТИЧЕСКИЙ СОСТАВ (исключая тренеров):")
        print("=" * 50)

        pos = 1
        for row in actual_placement:
            for cell in row:
                player_id = cell.get("id")
                position_id = cell.get("position_id")

                if player_id and position_id not in EXCLUDED_POSITIONS:
                    actual_players.append(player_id)

                    try:
                        player_obj = Player.objects.get(id=player_id)
                        print(f"{pos:2d}. {player_obj.name} {player_obj.surname}")
                        pos += 1
                    except:
                        print(f"{pos:2d}. Игрок ID: {player_id}")
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

        if matches:
            print(f"\n✅ УГАДАННЫЕ ИГРОКИ ({len(matches)}):")
            for player_id in matches:
                try:
                    player_obj = Player.objects.get(id=player_id)
                    pred_player = next((p for p in predicted_lineup if p['id'] == player_id), None)
                    prob = pred_player['probability'] if pred_player else 0
                    print(f"    ✅ {player_obj.name} {player_obj.surname} ({prob:.1%})")
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


def main():
    """Главная функция с валидацией"""
    print("=== SKLEARN AI + ВАЛИДАЦИЯ ПОЗИЦИЙ ===")
    print("🎯 Ансамбль из 5 моделей + умная проверка позиций")
    print("📚 Исправление нереалистичных предсказаний")

    while True:
        print("\n🎮 ВЫБЕРИТЕ РЕЖИМ:")
        print("1. Предсказание с валидацией позиций")
        print("2. Сравнение: с валидацией VS без валидации")
        print("3. Информация о системе")
        print("4. Выход")

        choice = input("\nВаш выбор (1-4): ").strip()

        if choice == "1":
            try:
                game_id = input("ID игры: ").strip()
                if not game_id.isdigit():
                    print("❌ ID игры должен быть числом")
                    continue

                is_home = input("Домашняя команда? (y/n): ").strip().lower() == "y"
                predicted_lineup, lineup_by_lines, accuracy, validation_report = predict_sklearn_lineup_with_validation(
                    int(game_id), is_home)

                if lineup_by_lines:
                    print(f"\n📋 ФОРМАТ ДЛЯ ПРОГРАММИРОВАНИЯ:")
                    print("=" * 50)
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
                                'validation_report': validation_report,
                                'model_type': 'sklearn_ensemble_with_validation'
                            }

                            with open(filename, 'w', encoding='utf-8') as f:
                                json.dump(output_data, f, indent=2, ensure_ascii=False)
                            print(f"💾 Сохранено в файл: {filename}")
                        except Exception as e:
                            print(f"❌ Ошибка сохранения: {e}")

            except Exception as e:
                print(f"❌ Ошибка: {e}")

        elif choice == "2":
            print("🔍 СРАВНЕНИЕ: С ВАЛИДАЦИЕЙ VS БЕЗ ВАЛИДАЦИИ")
            try:
                game_id = input("ID игры для сравнения: ").strip()
                if not game_id.isdigit():
                    print("❌ ID игры должен быть числом")
                    continue

                is_home = input("Домашняя команда? (y/n): ").strip().lower() == "y"

                print("\n" + "=" * 80)
                print("🤖 ПРЕДСКАЗАНИЕ БЕЗ ВАЛИДАЦИИ:")
                print("=" * 80)

                # Здесь бы вызвали оригинальную функцию predict_sklearn_lineup
                # original_lineup, original_lines, original_accuracy = predict_sklearn_lineup(int(game_id), is_home)
                print("(Для демонстрации - запустите оригинальную функцию)")

                print("\n" + "=" * 80)
                print("🔍 ПРЕДСКАЗАНИЕ С ВАЛИДАЦИЕЙ:")
                print("=" * 80)

                validated_lineup, validated_lines, validated_accuracy, val_report = predict_sklearn_lineup_with_validation(
                    int(game_id), is_home)

                print(f"\n📊 СРАВНЕНИЕ РЕЗУЛЬТАТОВ:")
                print(f"    Валидация исправила: {val_report.get('corrected_predictions', 0)} предсказаний")
                print(
                    f"    Процент корректировок: {val_report.get('corrected_predictions', 0) / max(val_report.get('total_players', 1), 1) * 100:.1f}%")

            except Exception as e:
                print(f"❌ Ошибка сравнения: {e}")

        elif choice == "3":
            print(f"\n📊 ИНФОРМАЦИЯ О СИСТЕМЕ:")
            print("=" * 60)
            print(f"🎯 Тип: Sklearn ансамбль + валидация позиций")
            print(f"🧠 Базовые модели: RF + ET + GB + LR + NN")
            print(f"🔍 Валидация: Проверка реальных позиций игроков")
            print(f"📈 Улучшения:")
            print(f"    ✅ Исключение нереалистичных назначений")
            print(f"    ✅ Использование данных последней игры")
            print(f"    ✅ Проверка основных и дополнительных позиций")
            print(f"    ✅ Учет состояния здоровья игроков")
            print(f"    ✅ Автоматическая замена некорректных предсказаний")

        elif choice == "4":
            print("👋 До свидания!")
            print("🎯 Система с валидацией готова к работе!")
            print("⚽ Реалистичные составы гарантированы!")
            break

        else:
            print("❌ Выберите от 1 до 4")


if __name__ == "__main__":
    main()