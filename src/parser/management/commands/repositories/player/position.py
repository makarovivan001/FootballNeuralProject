from player.models import Position


class ParserPlayerPositionRepository:
    def __init__(
            self
    ):
        ...

    async def get_or_create(self, position_title: str) -> int:
        position, created = await Position.objects.aget_or_create(
            name=position_title,
        )

        return position.id