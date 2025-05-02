from django.urls import path, include
from game.views.template import GameTemplatesViewSet


urlpatterns = [
    path('<int:game_id>/', GameTemplatesViewSet.as_view({
        'get': 'get_page'
    }))
]