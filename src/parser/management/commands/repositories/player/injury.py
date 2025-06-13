from player.models import Injury


class ParserPlayerInjuryRepository:
    def __init__(
            self
    ):
        ...

    async def get_or_create(self, injury_title: str, injury_id: int | None = None) -> int:
        if injury_id:
            injury, created = await Injury.objects.aget_or_create(
                name=injury_title,
                id=injury_id,
            )
        else:
            injury, created = await Injury.objects.aget_or_create(
                name=injury_title,
            )

        return injury.id