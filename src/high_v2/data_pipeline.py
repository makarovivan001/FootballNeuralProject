# new_data_pipeline.py - Исправленная версия для новой структуры Player

import numpy as np
import pandas as pd
from django.db import models
from django.db.models import Q
from tqdm import tqdm
from game.models import Game, GameStatistic
from player.models import Player, Position, PlayerGameStatistic

# ==== Константы ====
SEQ_LEN = 10
CLUB_STATS_DIM = 6
PG_FIELDS = [f.name for f in PlayerGameStatistic._meta.fields
             if f.name not in ("id", "game", "player")]
F_STATS = CLUB_STATS_DIM + len(PG_FIELDS)
OV_FIELDS = [f.name for f in Player._meta
.get_field("statistic")
.related_model._meta.fields
             if f.name not in ("id", "player")]
OV_STATS_DIM = len(OV_FIELDS)
MAX_PLAYERS = 11
PLACE_IN_DIM = MAX_PLAYERS * 2

# ИСПРАВЛЕНИЕ: Создаем правильные словари позиций
print("🎯 Создаем корректные словари позиций...")
all_position_ids = set([0])  # Добавляем 0 для случаев "нет позиции"

# Собираем все уникальные position_id из игр
games_with_placements = Game.objects.filter(
    home_club_placement__isnull=False,
    away_club_placement__isnull=False
).values('home_club_placement', 'away_club_placement')

for game in games_with_placements:
    for placement_field in ['home_club_placement', 'away_club_placement']:
        placement = game[placement_field]
        if placement:
            for row in placement:
                for player_info in row:
                    pos_id = player_info.get('position_id', 0)
                    if pos_id:
                        all_position_ids.add(pos_id)

# Также добавляем все ID из таблицы Position
db_position_ids = Position.objects.values_list('id', flat=True)
all_position_ids.update(db_position_ids)

# Сортируем для стабильности
sorted_position_ids = sorted(all_position_ids)
POS2IDX = {pos_id: idx for idx, pos_id in enumerate(sorted_position_ids)}
IDX2POS = {idx: pos_id for pos_id, idx in POS2IDX.items()}

print(f"✅ Создано {len(sorted_position_ids)} позиций: {sorted_position_ids[10:]}...")

# ИСПРАВЛЕНИЕ: Для игроков теперь НЕ исключаем никого по позиции, так как position теперь ManyToMany
player_ids = [0] + list(Player.objects.order_by("id").values_list("id", flat=True))
PLAYER2IDX = {pid: i for i, pid in enumerate(player_ids)}
IDX2PLAYER = {i: pid for pid, i in PLAYER2IDX.items()}


def safe_float(x, default=0.0):
    try:
        v = float(x) if x is not None else default
        if np.isnan(v) or np.isinf(v):
            return default
        return np.clip(v, -1e6, 1e6)
    except:
        return default


def slot_sequence(flat):
    """
    Из flat=[id1,pos1,id2,pos2,...] делаем ровно SEQ_LEN пар [id,pos].
    Берём первые SEQ_LEN, дополняем нулями.
    """
    pairs = [flat[i * 2:(i + 1) * 2] for i in range(MAX_PLAYERS)]
    seq = pairs[:SEQ_LEN]
    while len(seq) < SEQ_LEN:
        seq.append([0, 0])
    return seq


def flatten_placement(js):
    """
    js = список рядов [[{"id":..,"position_id":..},...], ...]
    Возвращает flat = [id1,pos1,id2,pos2,...] ровно длины PLACE_IN_DIM,
    дополняя нулями в конце.
    """
    flat = []
    if js:
        for row in js:
            for c in row:
                flat += [c.get("id", 0), c.get("position_id", 0)]
                if len(flat) >= PLACE_IN_DIM:
                    break
            if len(flat) >= PLACE_IN_DIM:
                break

    # дополняем нулями до нужной длины
    if len(flat) < PLACE_IN_DIM:
        flat += [0] * (PLACE_IN_DIM - len(flat))
    return flat[:PLACE_IN_DIM]


def extract_club_stats(game, club):
    try:
        gs = GameStatistic.objects.get(game=game, club=club)
        return [
            safe_float(gs.corners),
            safe_float(gs.total_shots),
            safe_float(gs.shots_on_target),
            safe_float(gs.shots_off_target),
            safe_float(gs.accurate_passes_persent),
            safe_float(gs.tackles_succeeded_persent),
        ]
    except GameStatistic.DoesNotExist:
        return [0.0] * CLUB_STATS_DIM


def extract_playergame_stats(game, club):
    qs = PlayerGameStatistic.objects.filter(
        game=game, player__club=club
    )
    out = []
    for fld in PG_FIELDS:
        vals = []
        for pg in qs:
            v = getattr(pg, fld)
            if v is None:
                continue
            if isinstance(v, str) and "/" in v:
                a, b = v.split("/", 1)
                a, b = safe_float(a), safe_float(b)
                vals.append(a / (a + b) if (a + b) > 0 else 0.0)
            else:
                vals.append(safe_float(v))
        out.append(np.mean(vals) if vals else 0.0)
    return out


def extract_overall(club):
    """ИСПРАВЛЕНИЕ: Обновлено для новой структуры Player без фильтрации по position_id"""
    qs = Player.objects.filter(
        club=club, statistic__isnull=False
    ).select_related("statistic")
    out = []
    for fld in OV_FIELDS:
        vals = [safe_float(getattr(p.statistic, fld))
                for p in qs if getattr(p.statistic, fld) is not None]
        out.append(np.mean(vals) if vals else 0.0)
    return out


def aggregate_seq_stats(club, date):
    """Агрегирует статистику команды за последние SEQ_LEN игр до указанной даты"""
    past_ids = (
        GameStatistic.objects
        .filter(club=club, game__game_date__lt=date)
        .order_by("-game__game_date")
        .values_list("game", flat=True)[:SEQ_LEN]
    )
    seq = []
    for gid in past_ids:
        try:
            g = Game.objects.get(pk=gid)
            seq.append(extract_club_stats(g, club)
                       + extract_playergame_stats(g, club))
        except Game.DoesNotExist:
            seq.append([0.0] * F_STATS)
    while len(seq) < SEQ_LEN:
        seq.append([0.0] * F_STATS)
    return np.array(seq, dtype=np.float32)


def extract_formation(js):
    """
    js = placement_out JSON: возвращает кортеж длин рядов, напр. (1,4,4,2)
    """
    if not js:
        return ()
    lengths = [len(row) for row in js]
    return tuple(lengths)


def get_opponent_placements_history(club, date, limit=10):
    """
    Получает историю расстановок команды за последние limit игр
    Возвращает список расстановок соперников против этой команды
    """
    past_games = Game.objects.filter(
        game_date__lt=date,
        is_finished=True
    ).filter(
        models.Q(home_club=club) | models.Q(away_club=club)
    ).order_by("-game_date")[:limit]

    opp_placements = []
    for game in past_games:
        if game.home_club == club:
            # Клуб играл дома, берем расстановку гостей
            opp_placement = game.away_club_placement
        else:
            # Клуб играл в гостях, берем расстановку хозяев
            opp_placement = game.home_club_placement

        if opp_placement:
            flat_placement = flatten_placement(opp_placement)
            # ИСПРАВЛЕНИЕ: Используем правильные словари для преобразования
            flat_indexed = []
            for i in range(0, len(flat_placement), 2):
                player_id = flat_placement[i]
                pos_id = flat_placement[i + 1] if i + 1 < len(flat_placement) else 0
                player_idx = PLAYER2IDX.get(player_id, 0)
                pos_idx = POS2IDX.get(pos_id, 0)  # Используем правильный словарь
                flat_indexed.extend([player_idx, pos_idx])
            opp_placements.append(slot_sequence(flat_indexed))

    # Дополняем до нужного количества
    while len(opp_placements) < limit:
        opp_placements.append([[0, 0]] * SEQ_LEN)

    # Возвращаем массив размера (limit, SEQ_LEN, 2)
    result = np.array(opp_placements[:limit], dtype=np.float32)
    # Проверяем и исправляем размерность
    if result.shape != (limit, SEQ_LEN, 2):
        # Создаем правильный массив
        correct_result = np.zeros((limit, SEQ_LEN, 2), dtype=np.float32)
        for i, placement in enumerate(opp_placements[:limit]):
            placement_array = np.array(placement, dtype=np.float32)
            if placement_array.shape == (SEQ_LEN, 2):
                correct_result[i] = placement_array
        result = correct_result

    return result


# НОВЫЕ ФУНКЦИИ для работы с масками команд
def create_club_player_mask(club_id):
    """ИСПРАВЛЕНИЕ: Создает маску игроков для конкретной команды с учетом новой структуры"""
    club_players = Player.objects.filter(club_id=club_id).values_list('id', flat=True)
    mask = np.zeros(len(PLAYER2IDX), dtype=np.float32)

    for player_id in club_players:
        player_idx = PLAYER2IDX.get(player_id, 0)
        if 0 < player_idx < len(mask):  # Исключаем индекс 0 (неизвестный игрок)
            mask[player_idx] = 1.0

    return mask


def analyze_training_data(df):
    """Анализирует качество обучающих данных"""
    print("🔍 Анализ качества данных...")

    # Проверяем распределение игроков по командам
    players_per_team = {}
    for _, row in df.iterrows():
        club_id = row['club_id']
        if club_id not in players_per_team:
            club_players = Player.objects.filter(club_id=club_id).count()
            players_per_team[club_id] = club_players

    print(f"📊 Статистика игроков по командам:")
    print(f"    Средне игроков на команду: {np.mean(list(players_per_team.values())):.1f}")
    print(f"    Мин/Макс игроков: {min(players_per_team.values())}-{max(players_per_team.values())}")

    # Проверяем частоту использования игроков
    player_frequency = {}
    for _, row in df.iterrows():
        for player_idx in row['y_players']:
            player_frequency[player_idx] = player_frequency.get(player_idx, 0) + 1

    print(f"📊 Топ-10 самых используемых игроков:")
    top_players = sorted(player_frequency.items(), key=lambda x: x[1], reverse=True)[:10]
    for player_idx, count in top_players:
        player_id = IDX2PLAYER.get(player_idx, 0)
        player_obj = Player.objects.filter(id=player_id).first()
        name = f"{player_obj.name} {player_obj.surname}" if player_obj else f"ID:{player_id}"
        print(f"    {name}: {count} игр")

    # НОВОЕ: Анализ позиций игроков
    print(f"📊 Анализ позиций игроков:")
    players_with_positions = Player.objects.filter(
        primary_position__isnull=False
    ).select_related('primary_position')

    position_counts = {}
    for player in players_with_positions:
        pos_name = player.primary_position.name
        position_counts[pos_name] = position_counts.get(pos_name, 0) + 1

    print(f"    Топ-5 основных позиций:")
    top_positions = sorted(position_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    for pos_name, count in top_positions:
        print(f"      {pos_name}: {count} игроков")

    # Проверяем игроков без травм
    healthy_players = Player.objects.filter(injury__isnull=True).count()
    total_players = Player.objects.count()
    print(f"📊 Здоровые игроки: {healthy_players}/{total_players} ({healthy_players / total_players * 100:.1f}%)")

    return players_per_team


def get_player_position_compatibility(player_id, target_position_id):
    """
    НОВАЯ ФУНКЦИЯ: Проверяет совместимость игрока с позицией
    Возвращает скор от 0 до 1
    """
    try:
        player = Player.objects.get(id=player_id)

        # Проверяем основную позицию
        if player.primary_position and player.primary_position.id == target_position_id:
            return 1.0

        # Проверяем дополнительные позиции
        if player.position.filter(id=target_position_id).exists():
            return 0.8

        # Если нет прямого совпадения, возвращаем низкий скор
        return 0.1

    except Player.DoesNotExist:
        return 0.0


def build_raw_rows():
    """
    Собирает DataFrame со всеми фичами и таргетами
    ИСПРАВЛЕНИЕ: Теперь корректно сопоставляет ID позиций с индексами нейросети
    """
    print("📊 Загружаем игры из базы данных...")

    rows = []
    games = Game.objects.filter(
        game_date__year__gte=2010, is_finished=True
    ).select_related("home_club", "away_club")

    total_games = games.count()
    print(f"🎮 Найдено {total_games} завершенных игр с 2010 года")

    # Предварительно извлекаем общую статистику для всех команд
    print("📈 Извлекаем общую статистику команд...")
    all_clubs = set()
    for g in games:
        all_clubs.add(g.home_club)
        all_clubs.add(g.away_club)

    club_overall_cache = {}
    for club in tqdm(all_clubs, desc="Статистика команд"):
        club_overall_cache[club.id] = extract_overall(club)

    print("🔄 Обрабатываем каждую игру...")

    for g in tqdm(games, desc="Обработка игр", total=total_games):
        # Используем кешированную статистику
        home_overall = club_overall_cache[g.home_club.id]
        away_overall = club_overall_cache[g.away_club.id]

        for is_home in (True, False):
            club = g.home_club if is_home else g.away_club  # команда для прогноза
            opp = g.away_club if is_home else g.home_club  # соперник

            # ЦЕЛЕВАЯ расстановка (то, что мы предсказываем)
            placement_out_js = (
                g.home_club_placement if is_home else g.away_club_placement
            )

            # Пропускаем игры без расстановки
            if not placement_out_js:
                continue

            # ВХОДНАЯ расстановка соперника (известная) - преобразуем в индексы
            opp_placement_js = (
                g.away_club_placement if is_home else g.home_club_placement
            )
            flat_opp = flatten_placement(opp_placement_js)

            # ИСПРАВЛЕНИЕ: Используем правильные словари для преобразования
            flat_opp_indexed = []
            for i in range(0, len(flat_opp), 2):
                player_id = flat_opp[i]
                pos_id = flat_opp[i + 1] if i + 1 < len(flat_opp) else 0
                player_idx = PLAYER2IDX.get(player_id, 0)
                pos_idx = POS2IDX.get(pos_id, 0)  # Используем правильный словарь
                flat_opp_indexed.extend([player_idx, pos_idx])

            opp_placement_seq = slot_sequence(flat_opp_indexed)

            # ИСПРАВЛЕНИЕ: Целевые метки тоже используют правильные словари
            flat_out = flatten_placement(placement_out_js)
            y_players, y_positions = [], []
            for i in range(0, PLACE_IN_DIM, 2):
                player_id = flat_out[i]
                pos_id = flat_out[i + 1] if i + 1 < len(flat_out) else 0
                y_players.append(PLAYER2IDX.get(player_id, 0))
                y_positions.append(POS2IDX.get(pos_id, 0))  # Используем правильный словарь

            # Статистика команды за последние 10 игр
            club_seq_stats = aggregate_seq_stats(club, g.game_date)

            # Статистика соперника за последние 10 игр
            opp_seq_stats = aggregate_seq_stats(opp, g.game_date)

            # История расстановок соперников против этой команды
            opp_placements_history = get_opponent_placements_history(club, g.game_date)

            # Общая статистика команд
            club_overall = home_overall if is_home else away_overall
            opp_overall = away_overall if is_home else home_overall

            # Временные признаки
            m, d = g.game_date.month, g.game_date.weekday()
            date_feats = [
                safe_float(np.sin(2 * np.pi * m / 12)),
                safe_float(np.cos(2 * np.pi * m / 12)),
                safe_float(np.sin(2 * np.pi * d / 7)),
                safe_float(np.cos(2 * np.pi * d / 7)),
            ]

            formation = extract_formation(placement_out_js)

            rows.append({
                "game_date": g.game_date,
                "club_id": club.id,
                "opp_id": opp.id,
                "date_feats": date_feats,
                "club_overall_stats": club_overall,
                "opp_overall_stats": opp_overall,
                "club_seq_stats": club_seq_stats.tolist(),
                "opp_seq_stats": opp_seq_stats.tolist(),
                "opp_placement_input": opp_placement_seq,
                "opp_placements_history": opp_placements_history.tolist(),
                "y_players": y_players,
                "y_positions": y_positions,
                "placement_out_js": placement_out_js,
                "formation": formation,
            })

    print(f"✅ Собрано {len(rows)} строк данных")
    print(f"📊 Статистика позиций: всего {len(POS2IDX)} уникальных позиций")
    print(f"📊 Статистика игроков: всего {len(PLAYER2IDX)} игроков")
    return pd.DataFrame(rows)


def time_split(df):
    """Разделяет данные по годам для обучения/валидации/тестирования"""
    df = df.sort_values("game_date")
    train = df[df.game_date.dt.year <= 2023]
    val = df[df.game_date.dt.year == 2024]
    test = df[df.game_date.dt.year == 2025]
    return train.reset_index(drop=True), \
        val.reset_index(drop=True), \
        test.reset_index(drop=True)