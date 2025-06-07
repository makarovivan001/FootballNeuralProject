from datetime import datetime

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
                Game.objects.select_related(
                    "home_club",
                    "away_club"
                ).aget(id=game_id)
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
        ).select_related(
                    "home_club",
                    "away_club"
                )

        return [
            GameShortRetrieveDTO.model_validate(game)
            async for game in games
        ]

    async def get_by_player_id(
            self,
            player_id: int
    ) -> list[GameShortRetrieveDTO]:
        games = Game.objects.filter(
            Q(Q(home_players__contains=[player_id]) | Q(away_players__contains=[player_id])),
            is_finished=True
        ).select_related(
            "home_club",
            "away_club"
        ).order_by('-game_date')

        return [
            GameShortRetrieveDTO.model_validate(game)
            async for game in games[:10]
        ]

    async def get_near_games(self) -> list[dict]:
        current_date = datetime.now().date()

        past_games = Game.objects.filter(
            game_date__lte=current_date,
            is_finished=True
        ).select_related(
            "home_club",
            "away_club"
        ).order_by('-game_date')[:240]

        future_games = Game.objects.filter(
            game_date__gte=current_date,
            is_finished=False
        ).select_related(
            "home_club",
            "away_club"
        ).order_by('-game_date')[:3]

        past_games_list = [
            GameRetrieveDTO.model_validate(game).model_dump()
            async for game in past_games
        ]

        future_games_list = [
            GameRetrieveDTO.model_validate(game).model_dump()
            async for game in future_games
        ]

        return past_games_list + future_games_list

    async def get_by_season_id(self, season_id: int) -> list[GameShortRetrieveDTO]:
        games = Game.objects.filter(
            season_id=season_id,
            is_finished=True,
        ).select_related(
            "home_club",
            "away_club"
        )

        games_dto = [
            GameShortRetrieveDTO.model_validate(game)
            async for game in games
        ]

        return games_dto

    async def get_last_placement(
            self,
            club_id: int
    ) -> list:
        game = await Game.objects.filter(
            Q(home_club_id=club_id) | Q(away_club_id=club_id),
            is_finished=True
        ).order_by('-game_date').afirst()

        if game.home_club_id == club_id:
            return game.home_club_placement
        else:
            return game.away_club_placement
