from domain.interfaces.repositories.game.history import IHistoryRepository
from domain.schemas.game.history import HistoryRetrieveDTO
from game.models import History


class HistoryRepository(IHistoryRepository):
    async def get_for_game(
            self,
            game_id: int,
    ) -> list[HistoryRetrieveDTO]:
        histories = History.objects.filter(
            game_id=game_id,
        )

        return [
            HistoryRetrieveDTO.model_validate(history)
            async for history in histories
        ]