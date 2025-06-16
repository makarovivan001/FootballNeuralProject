# main.py - Исправленная версия с обработкой ошибок
from datetime import datetime
import logging
import os

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

# Настройка логирования
logger = logging.getLogger(__name__)

# Глобальные переменные для кеширования
predictor = None
finetuner = None


def get_ai_page(request):
    """Отображает страницу AI интерфейса"""
    return render(request, 'ai.html', context={})


def get_predictor():
    """Получает экземпляр предиктора с безопасной загрузкой"""
    global predictor

    if predictor is None:
        try:
            # Проверяем наличие файлов модели
            model_files = [
                'src/neural_network/views/lineup_prediction_model.keras',
                'src/neural_network/views/lineup_prediction_model_finetuned.keras',
                'src/neural_network/views/best_lineup_model.h5'
            ]

            model_exists = any(os.path.exists(f) for f in model_files)
            scaler_exists = os.path.exists('src/neural_network/views/lineup_scaler.pkl')

            if not model_exists:
                logger.error("Файлы модели не найдены!")
                return None

            if not scaler_exists:
                logger.error("Файл скалера не найден!")
                return None

            # Импортируем и создаем предиктор
            from .predict_formation import TeamLineupPredictor
            predictor = TeamLineupPredictor()

            # Проверяем что модель загрузилась
            if predictor.model is None or predictor.scaler is None:
                logger.error("Модель не загружена правильно!")
                predictor = None
                return None

            logger.info("Предиктор успешно загружен")

        except ImportError as e:
            logger.error(f"Ошибка импорта predict_formation: {e}")
            return None
        except Exception as e:
            logger.error(f"Ошибка создания предиктора: {e}")
            predictor = None
            return None

    return predictor


def get_finetuner():
    """Получает экземпляр файнтюнера с безопасной загрузкой"""
    global finetuner

    if finetuner is None:
        try:
            predictor_instance = get_predictor()
            if predictor_instance is None:
                return None

            from .finetuning_system import ModelFinetuner
            finetuner = ModelFinetuner(predictor_instance)
            finetuner.load_correction_history()

            logger.info("Файнтюнер успешно загружен")

        except ImportError as e:
            logger.error(f"Ошибка импорта finetuning_system: {e}")
            return None
        except Exception as e:
            logger.error(f"Ошибка создания файнтюнера: {e}")
            finetuner = None
            return None

    return finetuner


@csrf_exempt
@require_http_methods(["POST"])
def predict_lineup_api(request):
    """API для получения предсказания состава с полной обработкой ошибок"""
    try:
        # Парсим JSON
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON format'
            }, status=400)

        # Получаем параметры
        game_id = data.get('game_id')
        predict_home = data.get('predict_home', True)

        if not game_id:
            return JsonResponse({
                'success': False,
                'error': 'game_id is required'
            }, status=400)

        # Проверяем что game_id - число
        try:
            game_id = int(game_id)
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'error': 'game_id must be a number'
            }, status=400)

        # Получаем предиктор
        predictor_instance = get_predictor()
        if predictor_instance is None:
            return JsonResponse({
                'success': False,
                'error': 'Model not available',
                'message': 'Модель не загружена. Запустите обучение.'
            }, status=503)

        # Делаем предсказание
        try:
            result = predictor_instance.predict_lineup(game_id, predict_home)
        except Exception as e:
            logger.error(f"Ошибка предсказания для игры {game_id}: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Prediction failed',
                'message': f'Не удалось сделать предсказание: {str(e)}'
            }, status=500)

        if result is None:
            return JsonResponse({
                'success': False,
                'error': 'Failed to generate prediction',
                'message': 'Модель вернула пустой результат'
            }, status=500)

        # Добавляем информацию о команде
        try:
            from club.models import Club
            club = Club.objects.get(id=result['club_id'])
            result['club_name'] = club.name
        except Exception:
            result['club_name'] = f"Команда {result['club_id']}"

        # Возвращаем успешный результат
        return JsonResponse({
            'success': True,
            'prediction': result
        })

    except Exception as e:
        logger.error(f"Неожиданная ошибка в predict_lineup_api: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error',
            'message': 'Внутренняя ошибка сервера'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def add_correction_api(request):
    """API для добавления коррекции"""
    try:
        data = json.loads(request.body)
        game_id = data.get('game_id')
        predict_home = data.get('predict_home', True)
        actual_placement = data.get('actual_placement')
        predicted_placement = data.get('predicted_placement')

        if not all([game_id, actual_placement]):
            return JsonResponse({
                'success': False,
                'error': 'game_id and actual_placement are required'
            }, status=400)

        finetuner_instance = get_finetuner()
        if finetuner_instance is None:
            return JsonResponse({
                'success': False,
                'error': 'Finetuner not available'
            }, status=503)

        # Если нет предсказанной расстановки, получаем её
        if not predicted_placement:
            predictor_instance = get_predictor()
            if predictor_instance:
                prediction_result = predictor_instance.predict_lineup(game_id, predict_home)
                if prediction_result:
                    predicted_placement = prediction_result['placement']
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'Failed to get current prediction'
                    }, status=500)

        success = finetuner_instance.add_correction(
            game_id, predicted_placement, actual_placement, predict_home
        )

        if success:
            return JsonResponse({
                'success': True,
                'message': 'Correction added successfully',
                'total_corrections': len(finetuner_instance.correction_history)
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Failed to add correction'
            }, status=500)

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        logger.error(f"Ошибка в add_correction_api: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def fine_tune_model_api(request):
    """API для дообучения модели"""
    try:
        data = json.loads(request.body)
        learning_rate = data.get('learning_rate', 0.0001)
        epochs = data.get('epochs', 10)

        finetuner_instance = get_finetuner()
        if finetuner_instance is None:
            return JsonResponse({
                'success': False,
                'error': 'Finetuner not available'
            }, status=503)

        if len(finetuner_instance.correction_history) == 0:
            return JsonResponse({
                'success': False,
                'error': 'No corrections available for fine-tuning'
            }, status=400)

        success = finetuner_instance.fine_tune_model(
            learning_rate=learning_rate,
            epochs=epochs
        )

        if success:
            # Перезагружаем предиктор с обновленной моделью
            global predictor
            predictor = None  # Сбрасываем кеш

            return JsonResponse({
                'success': True,
                'message': 'Model fine-tuned successfully',
                'corrections_used': len(finetuner_instance.correction_history),
                'learning_rate': learning_rate,
                'epochs': epochs
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Fine-tuning failed'
            }, status=500)

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        logger.error(f"Ошибка в fine_tune_model_api: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def get_correction_stats_api(request):
    """API для получения статистики коррекций"""
    try:
        finetuner_instance = get_finetuner()
        if finetuner_instance is None:
            return JsonResponse({
                'success': False,
                'error': 'Finetuner not available'
            }, status=503)

        # Статистика по командам
        club_stats = {}
        for correction in finetuner_instance.correction_history:
            club_id = correction.get('club_id')
            if club_id:
                if club_id not in club_stats:
                    club_stats[club_id] = 0
                club_stats[club_id] += 1

        # Статистика по времени  
        recent_corrections = []
        for correction in finetuner_instance.correction_history:
            try:
                timestamp = correction.get('timestamp')
                if timestamp and (datetime.now() - timestamp).days <= 7:
                    recent_corrections.append(correction)
            except:
                pass

        return JsonResponse({
            'success': True,
            'stats': {
                'total_corrections': len(finetuner_instance.correction_history),
                'recent_corrections': len(recent_corrections),
                'clubs_with_corrections': len(club_stats),
                'club_breakdown': club_stats,
                'model_exists': os.path.exists('lineup_prediction_model_finetuned.keras'),
                'backup_exists': os.path.exists('model_backup_before_finetune.keras')
            }
        })

    except Exception as e:
        logger.error(f"Ошибка в get_correction_stats_api: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def analyze_improvement_api(request):
    """API для анализа улучшений модели"""
    try:
        data = json.loads(request.body)
        game_id = data.get('game_id')
        predict_home = data.get('predict_home', True)

        if not game_id:
            return JsonResponse({
                'success': False,
                'error': 'game_id is required'
            }, status=400)

        finetuner_instance = get_finetuner()
        if finetuner_instance is None:
            return JsonResponse({
                'success': False,
                'error': 'Finetuner not available'
            }, status=503)

        result = finetuner_instance.evaluate_correction_impact(game_id, predict_home)

        if result is None:
            return JsonResponse({
                'success': False,
                'error': 'Failed to analyze improvement'
            }, status=500)

        return JsonResponse({
            'success': True,
            'analysis': result
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        logger.error(f"Ошибка в analyze_improvement_api: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def get_game_info_api(request, game_id):
    """API для получения информации об игре"""
    try:
        from game.models import Game
        from club.models import Club

        game = Game.objects.get(id=game_id)

        # Получаем информацию о командах
        home_club = Club.objects.get(id=game.home_club_id)
        away_club = Club.objects.get(id=game.away_club_id)

        return JsonResponse({
            'success': True,
            'game': {
                'id': game.id,
                'date': game.game_date.isoformat(),
                'tour': game.tour,
                'home_club': {
                    'id': home_club.id,
                    'name': home_club.name
                },
                'away_club': {
                    'id': away_club.id,
                    'name': away_club.name
                },
                'score': {
                    'home': game.home_score,
                    'away': game.away_score
                },
                'is_finished': game.is_finished,
                'has_home_placement': bool(game.home_club_placement),
                'has_away_placement': bool(game.away_club_placement)
            }
        })

    except Game.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Game not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Ошибка в get_game_info_api: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def export_corrections_api(request):
    """API для экспорта коррекций"""
    try:
        finetuner_instance = get_finetuner()
        if finetuner_instance is None:
            return JsonResponse({
                'success': False,
                'error': 'Finetuner not available'
            }, status=503)

        export_data = {
            'exported_at': datetime.now().isoformat(),
            'total_corrections': len(finetuner_instance.correction_history),
            'corrections': finetuner_instance.correction_history,
            'model_info': {
                'has_finetuned_model': os.path.exists('lineup_prediction_model_finetuned.keras'),
                'has_backup': os.path.exists('model_backup_before_finetune.keras'),
                'scaler_exists': os.path.exists('lineup_scaler.pkl')
            }
        }

        return JsonResponse({
            'success': True,
            'data': export_data
        })

    except Exception as e:
        logger.error(f"Ошибка в export_corrections_api: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)