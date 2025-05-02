from adrf.requests import AsyncRequest
from adrf.viewsets import ViewSet
from dependency_injector.wiring import Provide, inject
from django.shortcuts import render
from rest_framework.response import Response

from game.container import Container


class GameTemplatesViewSet(ViewSet):
    async def get_page(
            self,
            request: AsyncRequest,
            game_id: int
    ) -> render:
        context = {
            'game_id': game_id,
        }
        return render(request, 'game/index.html', context)