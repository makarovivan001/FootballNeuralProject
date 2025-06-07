from player.models import Role


class ParserPlayerRoleRepository:
    def __init__(
            self
    ):
        ...

    async def get_or_create(self, role_title: str) -> int:
        role, created = await Role.objects.aget_or_create(
            name=role_title,
        )

        return role.id