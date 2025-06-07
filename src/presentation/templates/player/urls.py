from django.urls import path, include
from player.views.template import PlayerTemplatesViewSet


urlpatterns = [
    path('<int:player_id>/', PlayerTemplatesViewSet.as_view({
        'get': 'get_page'
    }))

]