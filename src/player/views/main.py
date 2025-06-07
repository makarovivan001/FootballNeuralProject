from adrf.requests import AsyncRequest
from adrf.viewsets import ViewSet
from dependency_injector.wiring import Provide, inject
from rest_framework import status
from rest_framework.response import Response

from domain.interfaces.use_cases.player.main import IPlayerUseCase
from player.container import Container

class PlayerViewSet(ViewSet):
    @inject
    async def get_info(
            self,
            request: AsyncRequest,
            player_id: int,
            player_use_case: IPlayerUseCase = Provide[Container.player_use_case],
    ) -> Response:
        result = await player_use_case.get_info(player_id)

        return Response(result, status=status.HTTP_200_OK)
