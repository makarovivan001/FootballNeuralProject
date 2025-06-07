from application.services.common.custom_print import cprint
from domain.enums.print_colors import TextColor
from game.models import History, Action
from parser.management.commands.exceptions.main import GameNotFinishError, GameHistoryDoesNotExistError
from parser.management.commands.schemas.game.main import ParserGameShortRetrieveDTO


class ParserGameHistoryActionRepository:
    def __init__(
            self
    ) -> None:
        ...

    async def get_or_create(self, name: str) -> int:
        event_type, created = await Action.objects.aget_or_create(
            name=name,
        )

        return event_type.id