from django.urls import path, include
from .club.urls import urlpatterns as club_urls
from .common.urls import urlpatterns as common_urls
from .game.urls import urlpatterns as game_urls
from .player.urls import urlpatterns as player_urls


urlpatterns = [
    path('club/', include(club_urls)),
    path('common/', include(common_urls)),
    path('game/', include(game_urls)),
    path('player/', include(player_urls)),
]