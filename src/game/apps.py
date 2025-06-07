from django.apps import AppConfig


class GameConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'game'

    def ready(self):
        from .container import container
        from game import views as game_views
        container.wire(
            packages=[
                game_views,
            ]
        )
