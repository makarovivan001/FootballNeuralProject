from django.db.models import Q

from domain.exceptions.repositories.main import RepositoryConnectionDoesNotExistError
from domain.interfaces.repositories.game.main import IGameRepository
from domain.schemas.game.main import GameRetrieveDTO, GameShortRetrieveDTO
from game.models import Game


class GameRepository(IGameRepository):
    async def get_by_id(
            self,
            game_id: int
    ) -> GameRetrieveDTO:
        try:
            game = await (
                Game.objects
                .aget(id=game_id)
            )
            return GameRetrieveDTO.model_validate(game)
        except Game.DoesNotExist:
            raise RepositoryConnectionDoesNotExistError

    async def get_by_club_id(
            self,
            club_id: int
    ) -> list[GameShortRetrieveDTO]:
        games = Game.objects.filter(
            Q(home_club_id=club_id) | Q(away_club_id=club_id)
        )

        return [
            GameShortRetrieveDTO.model_validate(game)
            async for game in games
        ]