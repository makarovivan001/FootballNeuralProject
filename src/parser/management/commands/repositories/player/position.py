from player.models import Position


class ParserPlayerPositionRepository:
    def __init__(
            self
    ):
        ...

    async def get_or_create(self, position_title: str, position_id: int | None = None) -> int:
        if position_id:
            position, created = await Position.objects.aget_or_create(
                name=position_title,
                id=position_id,
            )
        else:
            position, created = await Position.objects.aget_or_create(
                name=position_title,
            )

        return position.id