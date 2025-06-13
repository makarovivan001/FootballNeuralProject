# position_validation.py - Логика валидации позиций для прогнозирования составов

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "football_main.settings")
django.setup()

from game.models import Game
from player.models import Player, Position
from club.models import Club
from django.db.models import Q


def get_last_game_lineup(club_id, before_date=None):
    """
    Получает состав клуба из последней игры

    Args:
        club_id: ID клуба
        before_date: Дата, до которой искать игры (для исключения текущей игры)

    Returns:
        dict: {position_id: player_id} из последней игры
    """
    try:
        # Находим последнюю игру клуба
        games_query = Game.objects.filter(
            Q(home_club_id=club_id) | Q(away_club_id=club_id),
            is_finished=True
        )

        if before_date:
            games_query = games_query.filter(game_date__lt=before_date)

        last_game = games_query.order_by('-game_date').first()

        if not last_game:
            return {}

        # Определяем, играл ли клуб дома или в гостях
        if last_game.home_club_id == club_id:
            placement = last_game.home_club_placement
        else:
            placement = last_game.away_club_placement

        if not placement:
            return {}

        # Извлекаем позиции и игроков
        last_game_lineup = {}
        for row in placement:
            for cell in row:
                player_id = cell.get("id")
                position_id = cell.get("position_id")
                if player_id and position_id:
                    last_game_lineup[position_id] = player_id

        return last_game_lineup

    except Exception as e:
        print(f"❌ Ошибка получения последней игры для клуба {club_id}: {e}")
        return {}


def check_player_position_compatibility(player_id, position_id):
    """
    Проверяет, играл ли игрок на указанной позиции

    Args:
        player_id: ID игрока
        position_id: ID позиции

    Returns:
        bool: True если игрок может играть на этой позиции
    """
    try:
        player = Player.objects.get(id=player_id)

        # Проверяем основную позицию
        if player.primary_position_id == position_id:
            return True

        # Проверяем дополнительные позиции (ManyToMany)
        if player.position.filter(id=position_id).exists():
            return True

        return False

    except Player.DoesNotExist:
        return False
    except Exception as e:
        print(f"❌ Ошибка проверки совместимости игрока {player_id} с позицией {position_id}: {e}")
        return False


def find_position_players_in_club(club_id, position_id):
    """
    Находит всех игроков клуба, которые могут играть на указанной позиции

    Args:
        club_id: ID клуба
        position_id: ID позиции

    Returns:
        list: Список ID игроков, которые могут играть на этой позиции
    """
    try:
        # Игроки с основной позицией
        primary_players = Player.objects.filter(
            club_id=club_id,
            primary_position_id=position_id,
            injury__isnull=True  # Исключаем травмированных
        ).values_list('id', flat=True)

        # Игроки с дополнительной позицией
        secondary_players = Player.objects.filter(
            club_id=club_id,
            position__id=position_id,
            injury__isnull=True  # Исключаем травмированных
        ).values_list('id', flat=True)

        # Объединяем и убираем дубликаты
        all_players = list(set(list(primary_players) + list(secondary_players)))

        return all_players

    except Exception as e:
        print(f"❌ Ошибка поиска игроков для позиции {position_id} в клубе {club_id}: {e}")
        return []


def validate_and_correct_predicted_lineup(predicted_lineup, club_id, game_date=None):
    """
    Валидирует и корректирует предсказанный состав на основе позиций игроков

    Args:
        predicted_lineup: Список словарей с предсказанным составом
                         [{'id': player_id, 'position_id': pos_id, 'name': name}, ...]
        club_id: ID клуба
        game_date: Дата игры (для поиска последней игры до этой даты)

    Returns:
        tuple: (corrected_lineup, validation_report)
    """
    print(f"🔍 Валидация предсказанного состава для клуба {club_id}")

    corrected_lineup = []
    validation_report = {
        'total_players': len(predicted_lineup),
        'valid_predictions': 0,
        'corrected_predictions': 0,
        'issues': []
    }

    # Получаем состав из последней игры
    last_game_lineup = get_last_game_lineup(club_id, game_date)
    print(f"📋 Последняя игра: найдено {len(last_game_lineup)} позиций")

    for i, player_data in enumerate(predicted_lineup):
        player_id = player_data.get('id')
        predicted_position_id = player_data.get('position_id')
        player_name = player_data.get('name', f'Player_{player_id}')

        print(f"\n🎯 Проверка {i + 1}/{len(predicted_lineup)}: {player_name} на позиции {predicted_position_id}")

        # 1. Проверяем, может ли предсказанный игрок играть на предсказанной позиции
        can_play_position = check_player_position_compatibility(player_id, predicted_position_id)

        if can_play_position:
            # Игрок может играть на этой позиции - принимаем предсказание
            print(f"✅ {player_name} может играть на позиции {predicted_position_id}")
            corrected_lineup.append(player_data)
            validation_report['valid_predictions'] += 1
        else:
            # Игрок не может играть на этой позиции - ищем замену
            print(f"❌ {player_name} не может играть на позиции {predicted_position_id}")

            # 2. Ищем всех игроков клуба, которые могут играть на этой позиции
            position_players = find_position_players_in_club(club_id, predicted_position_id)

            if not position_players:
                # Нет игроков для этой позиции - оставляем предсказание нейросети
                print(f"⚠️ В клубе нет игроков для позиции {predicted_position_id}, оставляем предсказание ИИ")
                corrected_lineup.append(player_data)
                validation_report['issues'].append({
                    'type': 'no_position_players',
                    'player_id': player_id,
                    'position_id': predicted_position_id,
                    'message': f'Нет игроков для позиции {predicted_position_id}'
                })
            else:
                # 3. Есть игроки для этой позиции - проверяем последнюю игру
                replacement_player_id = None

                # Сначала пытаемся найти игрока с этой позиции из последней игры
                if predicted_position_id in last_game_lineup:
                    last_game_player_id = last_game_lineup[predicted_position_id]
                    if last_game_player_id in position_players:
                        replacement_player_id = last_game_player_id
                        print(f"🔄 Заменяем на игрока из последней игры: {last_game_player_id}")

                # Если не нашли в последней игре, берем первого доступного
                if not replacement_player_id:
                    replacement_player_id = position_players[0]
                    print(f"🔄 Заменяем на первого доступного игрока: {replacement_player_id}")

                # Получаем информацию о игроке-замене
                try:
                    replacement_player = Player.objects.get(id=replacement_player_id)
                    replacement_name = f"{replacement_player.name} {replacement_player.surname}"
                except Player.DoesNotExist:
                    replacement_name = f"Player_{replacement_player_id}"

                corrected_player_data = {
                    'id': replacement_player_id,
                    'position_id': predicted_position_id,
                    'name': replacement_name
                }

                corrected_lineup.append(corrected_player_data)
                validation_report['corrected_predictions'] += 1
                validation_report['issues'].append({
                    'type': 'position_mismatch_corrected',
                    'original_player_id': player_id,
                    'corrected_player_id': replacement_player_id,
                    'position_id': predicted_position_id,
                    'message': f'Заменен {player_name} на {replacement_name}'
                })

                print(f"✅ Замена выполнена: {replacement_name} на позиции {predicted_position_id}")

    # Финальная статистика
    print(f"\n📊 ИТОГИ ВАЛИДАЦИИ:")
    print(f"    Всего игроков: {validation_report['total_players']}")
    print(f"    Валидных предсказаний: {validation_report['valid_predictions']}")
    print(f"    Исправлений: {validation_report['corrected_predictions']}")
    print(f"    Проблем: {len(validation_report['issues'])}")

    if validation_report['issues']:
        print(f"\n⚠️ ДЕТАЛИ ИСПРАВЛЕНИЙ:")
        for issue in validation_report['issues']:
            print(f"    {issue['message']}")

    return corrected_lineup, validation_report


def validate_lineup_by_lines(lineup_by_lines, club_id, game_date=None):
    """
    Валидирует состав, организованный по линиям

    Args:
        lineup_by_lines: Список линий с игроками
        club_id: ID клуба
        game_date: Дата игры

    Returns:
        tuple: (corrected_lineup_by_lines, validation_report)
    """
    # Преобразуем формат "по линиям" в плоский список
    flat_lineup = []
    for line in lineup_by_lines:
        for player in line:
            flat_lineup.append(player)

    # Валидируем плоский список
    corrected_flat_lineup, validation_report = validate_and_correct_predicted_lineup(
        flat_lineup, club_id, game_date
    )

    # Преобразуем обратно в формат "по линиям"
    corrected_lineup_by_lines = []
    flat_index = 0

    for line in lineup_by_lines:
        corrected_line = []
        for _ in line:
            if flat_index < len(corrected_flat_lineup):
                corrected_line.append(corrected_flat_lineup[flat_index])
                flat_index += 1
        corrected_lineup_by_lines.append(corrected_line)

    return corrected_lineup_by_lines, validation_report


def test_validation_logic():
    """Тестирует логику валидации на реальных данных"""
    print("🧪 ТЕСТИРОВАНИЕ ЛОГИКИ ВАЛИДАЦИИ")

    # Тестируем на реальной игре
    try:
        test_game = Game.objects.filter(
            home_club_placement__isnull=False,
            away_club_placement__isnull=False,
            is_finished=True
        ).first()

        if not test_game:
            print("❌ Не найдено подходящих игр для тестирования")
            return

        print(f"🎮 Тестовая игра: {test_game.home_club.name} vs {test_game.away_club.name}")

        # Берем реальный состав как "предсказание"
        test_placement = test_game.home_club_placement
        test_lineup = []

        for row in test_placement:
            for cell in row:
                player_id = cell.get("id")
                position_id = cell.get("position_id")
                if player_id and position_id:
                    try:
                        player = Player.objects.get(id=player_id)
                        test_lineup.append({
                            'id': player_id,
                            'position_id': position_id,
                            'name': f"{player.name} {player.surname}"
                        })
                    except Player.DoesNotExist:
                        test_lineup.append({
                            'id': player_id,
                            'position_id': position_id,
                            'name': f"Player_{player_id}"
                        })

        print(f"📋 Тестовый состав: {len(test_lineup)} игроков")

        # Применяем валидацию
        corrected_lineup, report = validate_and_correct_predicted_lineup(
            test_lineup, test_game.home_club.id, test_game.game_date
        )

        print(f"\n✅ Тест завершен успешно!")

    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")


# Пример интеграции с существующим кодом прогнозирования
def enhanced_predict_lineup(game_id, is_home=True):
    """
    Улучшенная функция прогнозирования с валидацией позиций
    Интегрируется с существующей функцией predict_sklearn_lineup
    """
    # Импортируем существующую функцию (в реальном коде это будет импорт)
    # from ai import predict_sklearn_lineup

    try:
        # Получаем базовое предсказание от нейросети
        print("🤖 Получаем предсказание от нейросети...")
        # predicted_lineup, lineup_by_lines, accuracy = predict_sklearn_lineup(game_id, is_home)

        # Для демонстрации создаем тестовые данные
        game = Game.objects.get(pk=game_id)
        club = game.home_club if is_home else game.away_club

        # Здесь была бы ваша существующая логика предсказания...
        # Для примера используем пустой список
        predicted_lineup = []
        lineup_by_lines = []

        print("🔍 Применяем валидацию позиций...")

        # Валидируем предсказание
        if lineup_by_lines:
            corrected_lineup_by_lines, validation_report = validate_lineup_by_lines(
                lineup_by_lines, club.id, game.game_date
            )
        else:
            corrected_lineup_by_lines = []
            validation_report = {'total_players': 0, 'valid_predictions': 0, 'corrected_predictions': 0, 'issues': []}

        # Также корректируем плоский список
        if predicted_lineup:
            corrected_predicted_lineup, _ = validate_and_correct_predicted_lineup(
                predicted_lineup, club.id, game.game_date
            )
        else:
            corrected_predicted_lineup = []

        print(f"✅ Валидация завершена:")
        print(f"    Исходных предсказаний: {validation_report['total_players']}")
        print(f"    Валидных: {validation_report['valid_predictions']}")
        print(f"    Исправлено: {validation_report['corrected_predictions']}")

        return corrected_predicted_lineup, corrected_lineup_by_lines, validation_report

    except Exception as e:
        print(f"❌ Ошибка улучшенного прогнозирования: {e}")
        return [], [], {}


if __name__ == "__main__":
    print("🎯 СИСТЕМА ВАЛИДАЦИИ ПОЗИЦИЙ")
    print("=" * 50)

    # Запускаем тест
    test_validation_logic()

    print(f"\n📚 ДОСТУПНЫЕ ФУНКЦИИ:")
    print(f"    validate_and_correct_predicted_lineup() - валидация плоского списка")
    print(f"    validate_lineup_by_lines() - валидация по линиям")
    print(f"    enhanced_predict_lineup() - прогнозирование с валидацией")
    print(f"    check_player_position_compatibility() - проверка совместимости")
    print(f"    find_position_players_in_club() - поиск игроков по позиции")
    print(f"    get_last_game_lineup() - состав из последней игры")