from adrf.requests import AsyncRequest
from adrf.viewsets import ViewSet
from dependency_injector.wiring import Provide, inject
from rest_framework import status
from rest_framework.response import Response

from club.container import Container
from domain.interfaces.use_cases.club.main import IClubUseCase


class ClubApiViewSet(ViewSet):
    @inject
    async def get_all(
            self,
            request: AsyncRequest,
            club_use_case: IClubUseCase = Provide[Container.club_use_case]
    ) -> Response:
        result = await club_use_case.get_all()
        return Response(data=result)

    @inject
    async def get_by_id(
            self,
            request: AsyncRequest,
            club_id: int,
            club_use_case: IClubUseCase = Provide[Container.club_use_case]
    ) -> Response:
        result = await club_use_case.get_page_info(
            request=request, club_id=club_id
        )

        return Response(data=result, status=status.HTTP_200_OK)