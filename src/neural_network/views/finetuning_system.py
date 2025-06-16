import os
import django
import numpy as np
import pickle
from datetime import datetime
from keras.models import load_model
from keras.optimizers import Adam
import json

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'football_statistics.settings')
django.setup()

from game.models import Game


class ModelFinetuner:
    def __init__(self, predictor_instance):
        self.predictor = predictor_instance
        self.correction_history = []

    def add_correction(self, game_id, predicted_placement, actual_placement, predict_home=True):
        """Добавляет коррекцию для дообучения - ИСПРАВЛЕННАЯ ВЕРСИЯ"""

        # Создаем признаки для этой игры
        features, club_id = self.predictor.create_prediction_features(game_id, predict_home)

        if features is None:
            print("Не удалось создать признаки для коррекции")
            return False

        # ВАЖНО: используем encode_placement (НЕ encode_placement_structured!)
        try:
            actual_encoded = self.predictor.encode_placement(actual_placement)
            predicted_encoded = self.predictor.encode_placement(predicted_placement)

            print(f"Кодировка успешна: actual={len(actual_encoded)}, predicted={len(predicted_encoded)}")

        except Exception as e:
            print(f"Ошибка кодировки расстановки: {e}")
            return False

        correction_data = {
            'game_id': game_id,
            'features': features,
            'actual_target': actual_encoded,
            'predicted_target': predicted_encoded,
            'predict_home': predict_home,
            'club_id': club_id,
            'timestamp': datetime.now()
        }

        self.correction_history.append(correction_data)
        print(f"✅ Добавлена коррекция для игры {game_id}")
        return True

    def fine_tune_model(self, learning_rate=0.0001, epochs=10):
        """Дообучает модель на корректировках"""

        if len(self.correction_history) == 0:
            print("❌ Нет данных для дообучения")
            return False

        print(f"🚀 Начинаем дообучение на {len(self.correction_history)} корректировках...")

        # Подготавливаем данные для дообучения
        X_corrections = []
        y_corrections = []

        for correction in self.correction_history:
            X_corrections.append(correction['features'])
            y_corrections.append(correction['actual_target'])

        X_corrections = np.array(X_corrections)
        y_corrections = np.array(y_corrections)

        print(f"📊 Размер данных: X={X_corrections.shape}, y={y_corrections.shape}")

        # Проверяем размерности
        if X_corrections.shape[1] != 433:
            print(f"❌ Неверный размер признаков: {X_corrections.shape[1]}, ожидается 433")
            return False

        if y_corrections.shape[1] != 33:
            print(f"❌ Неверный размер целевых переменных: {y_corrections.shape[1]}, ожидается 33")
            return False

        # Нормализуем признаки
        try:
            X_corrections_scaled = self.predictor.scaler.transform(X_corrections)
            print("✅ Данные нормализованы")
        except Exception as e:
            print(f"❌ Ошибка нормализации: {e}")
            return False

        # Сохраняем текущие веса как backup
        try:
            backup_path = self.predictor.get_file_path('model_backup_before_finetune.keras')
            self.predictor.model.save(backup_path)
            print(f"✅ Backup модели создан: {backup_path}")
        except Exception as e:
            print(f"⚠️  Предупреждение: не удалось создать backup: {e}")

        # Уменьшаем learning rate для fine-tuning
        try:
            self.predictor.model.compile(
                optimizer=Adam(learning_rate=learning_rate),
                loss='mse',
                metrics=['mae']
            )
            print(f"✅ Модель перекомпилирована с LR={learning_rate}")
        except Exception as e:
            print(f"❌ Ошибка компиляции модели: {e}")
            return False

        # Дообучаем модель
        try:
            print("🎯 Начинаем дообучение...")

            history = self.predictor.model.fit(
                X_corrections_scaled,
                y_corrections,
                epochs=epochs,
                batch_size=min(8, len(X_corrections)),
                verbose=1,
                validation_split=0.2 if len(X_corrections) > 5 else 0
            )

            # Сохраняем обновленную модель
            finetuned_path = self.predictor.get_file_path('lineup_prediction_model_finetuned.keras')
            self.predictor.model.save(finetuned_path)
            print(f"✅ Дообученная модель сохранена: {finetuned_path}")

            # Сохраняем историю корректировок
            history_path = self.predictor.get_file_path('correction_history.pkl')
            with open(history_path, 'wb') as f:
                pickle.dump(self.correction_history, f)
            print(f"✅ История корректировок сохранена: {history_path}")

            final_loss = history.history['loss'][-1]
            print(f"🎉 Дообучение завершено! Финальная ошибка: {final_loss:.4f}")

            # Показываем улучшение
            if len(history.history['loss']) > 1:
                initial_loss = history.history['loss'][0]
                improvement = ((initial_loss - final_loss) / initial_loss) * 100
                print(f"📈 Улучшение: {improvement:.1f}%")

            return True

        except Exception as e:
            print(f"❌ Ошибка дообучения: {e}")
            import traceback
            traceback.print_exc()
            return False

    def evaluate_correction_impact(self, game_id, predict_home=True):
        """Оценивает влияние коррекции на предсказания"""

        # Загружаем оригинальную модель
        try:
            backup_path = self.predictor.get_file_path('model_backup_before_finetune.keras')
            original_model = load_model(backup_path, compile=False)
            original_model.compile(optimizer=Adam(), loss='mse', metrics=['mae'])
            print("✅ Оригинальная модель загружена для сравнения")
        except Exception as e:
            print(f"⚠️  Оригинальная модель не найдена: {e}")
            return None

        # Создаем признаки
        features, club_id = self.predictor.create_prediction_features(game_id, predict_home)
        if features is None:
            return None

        try:
            features_scaled = self.predictor.scaler.transform(features.reshape(1, -1))

            # Предсказания оригинальной и обновленной моделей
            original_pred = original_model.predict(features_scaled, verbose=0)[0]
            updated_pred = self.predictor.model.predict(features_scaled, verbose=0)[0]

            # Анализируем различия
            diff = np.mean(np.abs(updated_pred - original_pred))

            return {
                'game_id': game_id,
                'club_id': club_id,
                'average_difference': float(diff),
                'improvement_percentage': float(diff * 100),
                'original_prediction_length': len(original_pred),
                'updated_prediction_length': len(updated_pred)
            }

        except Exception as e:
            print(f"❌ Ошибка анализа: {e}")
            return None

    def load_correction_history(self):
        """Загружает историю корректировок"""
        try:
            history_path = self.predictor.get_file_path('correction_history.pkl')
            with open(history_path, 'rb') as f:
                self.correction_history = pickle.load(f)
            print(f"✅ Загружено {len(self.correction_history)} корректировок")
        except FileNotFoundError:
            print("ℹ️  История корректировок не найдена (это нормально для первого запуска)")
            self.correction_history = []
        except Exception as e:
            print(f"❌ Ошибка загрузки истории: {e}")
            self.correction_history = []

    def get_statistics(self):
        """Получает статистику системы коррекций"""
        if not self.correction_history:
            return {
                'total_corrections': 0,
                'clubs': {},
                'recent_corrections': 0
            }

        # Статистика по командам
        clubs = {}
        recent_count = 0
        now = datetime.now()

        for correction in self.correction_history:
            club_id = correction.get('club_id')
            if club_id:
                clubs[club_id] = clubs.get(club_id, 0) + 1

            # Считаем недавние коррекции (за последнюю неделю)
            timestamp = correction.get('timestamp')
            if timestamp and (now - timestamp).days <= 7:
                recent_count += 1

        return {
            'total_corrections': len(self.correction_history),
            'clubs': clubs,
            'recent_corrections': recent_count
        }


def create_correction_interface():
    """Создает интерфейс для коррекции предсказаний"""

    print("🚀 ЗАПУСК СИСТЕМЫ КОРРЕКЦИЙ")
    print("=" * 50)

    # Импортируем предиктор
    try:
        from predict_formation import TeamLineupPredictor
        print("✅ TeamLineupPredictor импортирован")
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return

    # Создаем предиктор
    print("📦 Загрузка предиктора...")
    predictor = TeamLineupPredictor()

    if predictor.model is None or predictor.scaler is None:
        print("❌ Модель не загружена! Проверьте файлы модели.")
        print("💡 Возможные решения:")
        print("   1. Запустите: python train_formation_predictor.py")
        print("   2. Или создайте базовую модель: python setup_lineup_system.py")
        return

    print("✅ Предиктор успешно загружен")

    # Создаем файнтюнер
    finetuner = ModelFinetuner(predictor)
    finetuner.load_correction_history()

    while True:
        print("\n" + "=" * 50)
        print("🎯 СИСТЕМА КОРРЕКЦИИ ПРЕДСКАЗАНИЙ")
        print("=" * 50)
        print("1. ➕ Добавить коррекцию")
        print("2. 🧠 Выполнить дообучение")
        print("3. 📊 Показать статистику")
        print("4. 🔬 Анализ улучшений")
        print("5. 🚪 Выход")
        print("=" * 50)

        choice = input("Выберите действие (1-5): ").strip()

        if choice == '1':
            try:
                print("\n📝 ДОБАВЛЕНИЕ КОРРЕКЦИИ")
                print("-" * 30)

                game_id = input("ID игры: ").strip()
                if not game_id:
                    print("❌ ID игры не может быть пустым")
                    continue

                game_id = int(game_id)

                predict_home = input("Домашняя команда? (y/n): ").strip().lower() == 'y'

                print("🔄 Получаем текущее предсказание...")
                current_prediction = predictor.predict_lineup(game_id, predict_home)
                if not current_prediction:
                    print("❌ Не удалось получить предсказание")
                    continue

                print("\n🎯 Текущее предсказание:")
                predictor.visualize_lineup(current_prediction)

                print("\n📋 Введите фактическую расстановку в формате JSON:")
                print("💡 Пример: [[{'id': 4249, 'position_id': 11}], [{'id': 4262, 'position_id': 32}], ...]")

                actual_json = input("\nФактическая расстановка: ").strip()
                if not actual_json:
                    print("❌ Расстановка не может быть пустой")
                    continue

                try:
                    actual_placement = json.loads(actual_json)
                except json.JSONDecodeError as e:
                    print(f"❌ Неверный формат JSON: {e}")
                    continue

                # Валидация введенных данных
                if not isinstance(actual_placement, list):
                    print("❌ Ошибка: расстановка должна быть массивом")
                    continue

                total_players = sum(len(line) for line in actual_placement if isinstance(line, list))
                if total_players != 11:
                    print(f"❌ Ошибка: должно быть 11 игроков, а найдено {total_players}")
                    continue

                print("⚙️  Добавляем коррекцию...")
                success = finetuner.add_correction(
                    game_id,
                    current_prediction['placement'],
                    actual_placement,
                    predict_home
                )

                if success:
                    stats = finetuner.get_statistics()
                    print(f"🎉 Коррекция добавлена!")
                    print(f"📈 Всего корректировок: {stats['total_corrections']}")
                else:
                    print("❌ Не удалось добавить коррекцию")

            except ValueError:
                print("❌ Неверный ID игры (должно быть число)")
            except Exception as e:
                print(f"❌ Ошибка: {e}")

        elif choice == '2':
            stats = finetuner.get_statistics()
            if stats['total_corrections'] == 0:
                print("❌ Нет корректировок для дообучения")
                print("💡 Сначала добавьте хотя бы одну коррекцию (действие 1)")
                continue

            print(f"\n🧠 ДООБУЧЕНИЕ МОДЕЛИ")
            print("-" * 30)
            print(f"📊 Доступно корректировок: {stats['total_corrections']}")

            try:
                lr_input = input("Learning rate (по умолчанию 0.0001): ").strip()
                lr = float(lr_input) if lr_input else 0.0001

                epochs_input = input("Количество эпох (по умолчанию 10): ").strip()
                epochs = int(epochs_input) if epochs_input else 10

                if lr <= 0 or lr > 0.1:
                    print("❌ Learning rate должен быть между 0.0001 и 0.1")
                    continue

                if epochs < 1 or epochs > 100:
                    print("❌ Количество эпох должно быть между 1 и 100")
                    continue

                print(f"\n🚀 Запуск дообучения с параметрами:")
                print(f"   📐 Learning Rate: {lr}")
                print(f"   🔄 Эпохи: {epochs}")
                print(f"   📊 Корректировок: {stats['total_corrections']}")

                confirm = input("\nПродолжить? (y/n): ").strip().lower()
                if confirm != 'y':
                    print("❌ Дообучение отменено")
                    continue

                success = finetuner.fine_tune_model(learning_rate=lr, epochs=epochs)

                if success:
                    print("\n🎉 ДООБУЧЕНИЕ ЗАВЕРШЕНО УСПЕШНО!")

                    # Перезагружаем модель
                    try:
                        finetuned_path = predictor.get_file_path('lineup_prediction_model_finetuned.keras')
                        predictor.model = load_model(finetuned_path, compile=False)
                        from keras.optimizers import Adam
                        predictor.model.compile(
                            optimizer=Adam(learning_rate=0.001),
                            loss='mse',
                            metrics=['mae']
                        )
                        print("✅ Модель перезагружена с новыми весами")
                    except Exception as e:
                        print(f"⚠️  Предупреждение: не удалось перезагрузить модель: {e}")
                else:
                    print("❌ Дообучение не удалось")

            except ValueError:
                print("❌ Неверные параметры (должны быть числами)")
            except Exception as e:
                print(f"❌ Ошибка: {e}")

        elif choice == '3':
            print(f"\n📊 СТАТИСТИКА СИСТЕМЫ")
            print("-" * 30)

            stats = finetuner.get_statistics()

            print(f"📈 Всего корректировок: {stats['total_corrections']}")
            print(f"🕐 Недавних корректировок (7 дней): {stats['recent_corrections']}")
            print(f"⚽ Команд с корректировками: {len(stats['clubs'])}")

            if stats['clubs']:
                print(f"\n🏆 Корректировки по командам:")
                for club_id, count in sorted(stats['clubs'].items(), key=lambda x: x[1], reverse=True):
                    print(f"   Команда {club_id}: {count} корректировок")

            # Статистика файлов
            print(f"\n💾 Состояние файлов:")
            files_to_check = [
                ('lineup_prediction_model.keras', 'Основная модель'),
                ('lineup_prediction_model_finetuned.keras', 'Дообученная модель'),
                ('model_backup_before_finetune.keras', 'Backup модели'),
                ('correction_history.pkl', 'История коррекций'),
                ('lineup_scaler.pkl', 'Скалер'),
                ('normalization_info.pkl', 'Нормализация')
            ]

            for filename, description in files_to_check:
                file_path = predictor.get_file_path(filename)
                status = "✅" if os.path.exists(file_path) else "❌"
                print(f"   {status} {description}")

        elif choice == '4':
            print(f"\n🔬 АНАЛИЗ УЛУЧШЕНИЙ")
            print("-" * 30)

            try:
                test_game_id = input("ID игры для анализа: ").strip()
                if not test_game_id:
                    print("❌ ID игры не может быть пустым")
                    continue

                test_game_id = int(test_game_id)
                predict_home = input("Домашняя команда? (y/n): ").strip().lower() == 'y'

                print("🔄 Анализируем улучшения...")
                result = finetuner.evaluate_correction_impact(test_game_id, predict_home)

                if result:
                    print(f"\n📊 РЕЗУЛЬТАТ АНАЛИЗА:")
                    print(f"   🎯 Игра: {result['game_id']}")
                    print(f"   ⚽ Команда: {result['club_id']}")
                    print(f"   📈 Средняя разница: {result['average_difference']:.4f}")
                    print(f"   📊 Улучшение: {result['improvement_percentage']:.2f}%")
                else:
                    print("❌ Не удалось провести анализ")

            except ValueError:
                print("❌ Неверный ID игры (должно быть число)")
            except Exception as e:
                print(f"❌ Ошибка: {e}")

        elif choice == '5':
            print("\n👋 Выход из системы коррекции")
            print("🎉 Спасибо за использование!")
            break

        else:
            print("❌ Неверный выбор. Пожалуйста, выберите от 1 до 5.")


if __name__ == "__main__":
    try:
        create_correction_interface()
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback

        traceback.print_exc()