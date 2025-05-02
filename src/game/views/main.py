from adrf.requests import AsyncRequest
from adrf.viewsets import ViewSet
from dependency_injector.wiring import Provide, inject
from rest_framework import status
from rest_framework.response import Response

from domain.interfaces.use_cases.game.main import IGameUseCase
from game.container import Container


class GameViewSet(ViewSet):
    @inject
    async def get_info(
            self,
            request: AsyncRequest,
            game_id: int,
            game_use_case: IGameUseCase = Provide[Container.game_use_case]
    ) -> Response:
        result = await game_use_case.get_page_info(
            request=request, game_id=game_id
        )

        return Response(data={result}, status=status.HTTP_200_OK)

