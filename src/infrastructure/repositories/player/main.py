from django.db.models import Q
from pydantic import BaseModel

from domain.exceptions.repositories.main import RepositoryConnectionDoesNotExistError
from domain.interfaces.repositories.player.main import IPlayerRepository
from domain.schemas.player.main import PlayerStatsRetrieveDTO, PlayerRetrieveDTO, PlayerShortRetrieveDTO, \
    PlayerAllStatsRetrieveDTO
from player.models import Player


class PlayerRepository(IPlayerRepository):

    async def get_by_club_id(
        self,
        club_id: int,
        dto_model: BaseModel = PlayerStatsRetrieveDTO,
        param: Q = Q()
    ) -> list[PlayerStatsRetrieveDTO | PlayerShortRetrieveDTO]:
        players = Player.objects.select_related(
                "club", "statistic", "primary_position"
        ).filter(
            param,
            club_id=club_id,
        )

        return [
            dto_model.model_validate(player)
            async for player in players
        ]

    async def get_by_id(
            self,
            player_id: int
    ) -> PlayerRetrieveDTO:
        try:
            player = await (
                Player.objects
                .select_related('club', 'primary_position')
                .aget(id=player_id)
            )
            return PlayerRetrieveDTO.model_validate(player)
        except Player.DoesNotExist:
            raise RepositoryConnectionDoesNotExistError

    async def get_by_ids(
            self,
            player_ids: list[int],
            dto_model: BaseModel = PlayerAllStatsRetrieveDTO,
    ) -> dict[int, PlayerShortRetrieveDTO | PlayerAllStatsRetrieveDTO]:
        players = Player.objects.select_related("statistic", "club", 'primary_position').filter(
            id__in=player_ids
        )

        return {
            player.id: dto_model.model_validate(player)
            async for player in players
        }

    async def get_all(
            self
    ) -> list[PlayerAllStatsRetrieveDTO]:
        all_players = Player.objects.select_related(
            'club', 'statistic', 'primary_position'
        ).all()
        return [
            PlayerAllStatsRetrieveDTO.model_validate(player)
            async for player in all_players
        ]

    # async def get_by_two_ids(
    #         self,
    #         player_ids
    # ):