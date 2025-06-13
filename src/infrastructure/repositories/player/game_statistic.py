from domain.exceptions.repositories.main import RepositoryConnectionDoesNotExistError
from domain.interfaces.repositories.player.game_statistic import IPlayerGameStatisticRepository
from domain.schemas.player.game_statistic import PlayerGameStatisticRetrieveDTO, PlayerGameStatisticShortRetrieveDTO
from player.models import PlayerGameStatistic


class PlayerGameStatisticRepository(IPlayerGameStatisticRepository):
    async def get_for_game_page(
            self,
            game_id: int
    ) -> list[PlayerGameStatisticRetrieveDTO]:
        game_statistics = (
            PlayerGameStatistic.objects.select_related('player', 'player__primary_position').
            filter(game_id=game_id)
        )
        return [
            PlayerGameStatisticRetrieveDTO.model_validate(game_stats)
            async for game_stats in game_statistics
        ]

    async def get_for_player_page(
            self,
            player_id: int,
            game_ids: list[int]
    ) -> list[PlayerGameStatisticShortRetrieveDTO]:
        game_statistics = (
            PlayerGameStatistic.objects
            .filter(player_id=player_id, game_id__in=game_ids)
        )
        return [
            PlayerGameStatisticShortRetrieveDTO.model_validate(game_stats)
            async for game_stats in game_statistics
        ]
