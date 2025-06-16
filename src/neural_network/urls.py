from django.urls import path
from .views.main import *

urlpatterns = [
    path('template/ai/', get_ai_page),
    path('api/predict-lineup/', predict_lineup_api, name='predict_lineup_api'),
    path('api/add-correction/', add_correction_api, name='add_correction_api'),
    path('api/fine-tune/', fine_tune_model_api, name='fine_tune_model_api'),
    path('api/correction-stats/', get_correction_stats_api, name='correction_stats_api'),
    path('api/analyze-improvement/', analyze_improvement_api, name='analyze_improvement_api'),
    path('api/game-info/<int:game_id>/', get_game_info_api, name='game_info_api'),
    path('api/export-corrections/', export_corrections_api, name='export_corrections_api'),
]