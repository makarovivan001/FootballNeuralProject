from django.apps import AppConfig


class ClubConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'club'

    def ready(self):
        from .container import container
        from club import views as club_views
        container.wire(
            packages=[
                club_views,
            ]
        )
