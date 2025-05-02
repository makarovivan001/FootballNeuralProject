from domain.interfaces.repositories.player.main import IPlayerRepository
from domain.schemas.player.main import PlayerStatsRetrieveDTO
from player.models import Player


class PlayerRepository(IPlayerRepository):
    async def get_by_club_id(
            self,
            club_id: int
    ) -> list[PlayerStatsRetrieveDTO]:
        players = Player.objects.filter(
            club_id=club_id
        )

        return [
            PlayerStatsRetrieveDTO.model_validate(player)
            for player in players
        ]