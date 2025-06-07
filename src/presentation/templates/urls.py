from django.urls import path, include
from .club.urls import urlpatterns as club_templates_urls
from .game.urls import urlpatterns as game_templates_urls
from .player.urls import urlpatterns as player_templates_urls



urlpatterns = [
    path('', include(club_templates_urls)),
    path('game/', include(game_templates_urls)),
    path('player/', include(player_templates_urls)),
    path('', include(player_templates_urls)),

]