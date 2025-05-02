from django.urls import path, include

from game.views.main import GameViewSet

urlpatterns = [
    path('<int:game_id>/', GameViewSet.as_view({
        'get': 'get_info'
    })),
]