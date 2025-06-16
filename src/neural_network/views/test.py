# setup_lineup_system.py
"""
Скрипт для быстрой настройки системы предсказания составов
Запустите этот файл один раз для инициализации
"""

import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'football_statistics.settings')
django.setup()


def check_requirements():
    """Проверяет наличие необходимых файлов и данных"""
    print("🔍 Проверка системы...")

    # Проверяем наличие данных
    from game.models import Game

    total_games = Game.objects.count()
    games_with_data = Game.objects.filter(
        is_finished=True,
        home_club_placement__isnull=False,
        away_club_placement__isnull=False,
        home_players__isnull=False,
        away_players__isnull=False
    ).count()

    print(f"📊 Статистика данных:")
    print(f"   Всего игр: {total_games}")
    print(f"   Игр с полными данными: {games_with_data}")

    if games_with_data < 10:
        print("⚠️  Мало данных для обучения, будет создана базовая модель")
        return False

    print("✅ Достаточно данных для обучения")
    return True


def create_basic_model():
    """Создает базовую рабочую модель"""
    print("🔧 Создание базовой модели...")

    import numpy as np
    import pickle
    from sklearn.preprocessing import StandardScaler
    from keras.models import Sequential
    from keras.layers import Dense
    from keras.optimizers import Adam

    # Создаем простую модель
    model = Sequential([
        Dense(256, activation='relu', input_shape=(433,)),
        Dense(128, activation='relu'),
        Dense(64, activation='relu'),
        Dense(33, activation='sigmoid')
    ])

    model.compile(optimizer=Adam(learning_rate=0.001), loss='mse', metrics=['mae'])

    # Инициализируем на фиктивных данных
    X_dummy = np.random.random((50, 433))
    y_dummy = np.random.random((50, 33))

    print("   Обучение базовой модели...")
    model.fit(X_dummy, y_dummy, epochs=5, verbose=0)

    # Сохраняем модель
    model.save('lineup_prediction_model.keras')
    print("✅ Модель сохранена: lineup_prediction_model.keras")

    # Создаем скалер
    scaler = StandardScaler()
    scaler.fit(X_dummy)

    with open('lineup_scaler.pkl', 'wb') as f:
        pickle.dump(scaler, f)
    print("✅ Скалер сохранен: lineup_scaler.pkl")

    # Информация о нормализации
    normalization_info = {
        'player_id_min': 3000,
        'player_id_range': 4000,
        'position_id_max': 120,
        'line_max': 4.0
    }

    with open('normalization_info.pkl', 'wb') as f:
        pickle.dump(normalization_info, f)
    print("✅ Нормализация сохранена: normalization_info.pkl")


def train_real_model():
    """Обучает настоящую модель на реальных данных"""
    print("🎯 Обучение на реальных данных...")

    try:
        # Импортируем тренер
        from train_formation_predictor import TeamLineupPredictor

        predictor = TeamLineupPredictor()
        predictor.train()

        print("✅ Модель обучена на реальных данных!")
        return True

    except Exception as e:
        print(f"❌ Ошибка обучения: {e}")
        print("   Создается базовая модель...")
        return False


def test_prediction():
    """Тестирует систему предсказаний"""
    print("🧪 Тестирование системы...")

    try:
        from predict_formation import TeamLineupPredictor

        predictor = TeamLineupPredictor()

        # Проверяем загрузку модели
        if predictor.model is None or predictor.scaler is None:
            print("❌ Модель не загружена")
            return False

        print("✅ Модель успешно загружена")

        # Тестируем на игре 89
        result = predictor.predict_lineup(89, True)

        if result:
            print("✅ Предсказание работает!")
            print(f"   Команда: {result['club_id']}")
            print(f"   Уверенность: {result['prediction_confidence']:.2f}")
            return True
        else:
            print("❌ Предсказание не работает")
            return False

    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False


def setup_api():
    """Настраивает API"""
    print("🔌 Настройка API...")

    # Проверяем main.py
    if os.path.exists('main.py'):
        print("✅ main.py найден")
    else:
        print("❌ main.py не найден")
        return False

    # Проверяем HTML файл
    if os.path.exists('ai.html'):
        print("✅ ai.html найден")
    else:
        print("⚠️  ai.html не найден в корне")

    return True


def main():
    """Основная функция настройки"""
    print("=" * 60)
    print("🚀 НАСТРОЙКА СИСТЕМЫ ПРЕДСКАЗАНИЯ СОСТАВОВ")
    print("=" * 60)

    # Шаг 1: Проверка данных
    has_data = check_requirements()

    # Шаг 2: Обучение/создание модели
    if has_data:
        # Пытаемся обучить настоящую модель
        if not train_real_model():
            create_basic_model()
    else:
        # Создаем базовую модель
        create_basic_model()

    # Шаг 3: Тестирование
    if test_prediction():
        print("\n🎉 СИСТЕМА ГОТОВА К РАБОТЕ!")
    else:
        print("\n❌ Проблемы с системой")
        return False

    # Шаг 4: Настройка API
    setup_api()

    print("\n📋 СЛЕДУЮЩИЕ ШАГИ:")
    print("1. Запустите Django сервер")
    print("2. Откройте браузер на http://localhost:8000/ai/")
    print("3. Протестируйте предсказание для игры 89")
    print("4. При ошибках используйте систему коррекций")

    print("\n💡 ВАЖНЫЕ ФАЙЛЫ:")
    print("- lineup_prediction_model.keras (модель)")
    print("- lineup_scaler.pkl (нормализация)")
    print("- main.py (Django API)")
    print("- predict_formation.py (предсказания)")

    return True


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback

        traceback.print_exc()