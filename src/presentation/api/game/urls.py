from django.urls import path, include

from game.views.main import GameViewSet

urlpatterns = [
    path('<int:game_id>/', GameViewSet.as_view({
        'get': 'get_info'
    })),
    path('<int:game_id>/placement-probability/', GameViewSet.as_view({
        'get': 'get_placement_probability'
    })),
]