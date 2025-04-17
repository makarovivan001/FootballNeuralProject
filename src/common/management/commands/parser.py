from dependency_injector.wiring import inject, Provide
from django.core.management import BaseCommand
import requests
from bs4 import BeautifulSoup
from .parsers.container import Container
from .parsers.get_clubs import ClubsParser


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        container = Container()
        container.wire(modules=[__name__])
    # def add_arguments(self, parser):
        # parser.add_argument('-help', action='store_true')
        # parser.add_argument('-print', nargs='+', type=str)

    @inject
    def handle(
            self,
            get_clubs: ClubsParser = Provide[Container.get_clubs],
            *args,
            **options
    ):
        get_clubs.get_info()
        # self.stdout.write(self.style.ERROR(f'Parser ERROR...'))
        # self.stdout.write(self.style.SUCCESS(f'Parser started...'))

