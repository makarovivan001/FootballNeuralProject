from asgiref.sync import async_to_sync
from dependency_injector.wiring import inject, Provide
from django.core.management import BaseCommand

from parser.management.commands.container import Container
from parser.management.commands.use_cases.parser import ParserUseCase


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        container = Container()
        container.wire(modules=[__name__])

    @inject
    def handle(
            self,
            parser_use_case: ParserUseCase = Provide[Container.parser_use_case],
            *args,
            **options
    ):
        async_to_sync(parser_use_case.start)()

