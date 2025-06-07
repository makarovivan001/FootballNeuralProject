from django.urls import path, include

from player.views.main import PlayerViewSet

urlpatterns = [
    path('<int:player_id>/', PlayerViewSet.as_view({
        "get": "get_info",
    })),
]