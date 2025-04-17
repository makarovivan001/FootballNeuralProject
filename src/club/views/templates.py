from adrf.requests import AsyncRequest
from adrf.viewsets import ViewSet
from dependency_injector.wiring import Provide, inject
from django.shortcuts import render
from rest_framework.response import Response

from club.container import Container


class ClubTemplatesViewSet(ViewSet):
    @inject
    async def get_page(
            self,
            request: AsyncRequest,
            club_id: int
    ) -> render:
        context = {
            "club_id": club_id,
        }

        return render(request, "", context)