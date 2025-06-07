from adrf.requests import AsyncRequest
from adrf.viewsets import ViewSet
from dependency_injector.wiring import Provide, inject
from django.shortcuts import render
from rest_framework.response import Response

from game.container import Container


class PlayerTemplatesViewSet(ViewSet):
    async def get_page(
            self,
            request: AsyncRequest,
            player_id: int
    ) -> render:
        context = {
            'player_id': player_id,
        }
        return render(request, 'player/index.html', context)