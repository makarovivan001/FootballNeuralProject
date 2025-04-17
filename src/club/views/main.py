from adrf.requests import AsyncRequest
from adrf.viewsets import ViewSet
from dependency_injector.wiring import Provide, inject
from rest_framework.response import Response

from club.container import Container


class ClubViewSet(ViewSet):
    @inject
    async def get_all_clubs(
            self,
            request: AsyncRequest,
            club_use_case: IClubUseCase = Provide[Container.club_use_case]
    ) -> Response:
        ...