from domain.exceptions.repositories.main import RepositoryConnectionDoesNotExistError
from domain.exceptions.use_cases.common import RepositoryDoesNotExist
from domain.interfaces.repositories.game.main import IGameRepository
from domain.interfaces.repositories.player.game_statistic import IPlayerGameStatisticRepository
from domain.interfaces.repositories.player.main import IPlayerRepository
from domain.interfaces.repositories.player.statistic import IStatisticRepository
from domain.interfaces.use_cases.player.main import IPlayerUseCase

from domain.map import (
    center_back, full_back, wing_back,
    defensive_midfielder, central_midfielder, attacking_midfielder,
    side_midfielder, winger, striker, wide_midfielder, keeper
)
from domain.schemas.player.statistic import PlayerStatisticRetrieveDTO

POSITION_WEIGHT_MAP = {
    "Center Back": center_back.CENTER_BACK_WEIGHTS,
    "Full Back": full_back.FULL_BACK_WEIGHTS,
    "Half-Winger": wing_back.WING_BACK_WEIGHTS,
    "Defensive Midfielder": defensive_midfielder.DEFENSIVE_MIDFIELDER_WEIGHTS,
    "Wide Midfielder": wide_midfielder.WIDE_MIDFIELDER_WEIGHTS,
    "Central Midfielder": central_midfielder.CENTRAL_MIDFIELDER_WEIGHTS,
    "Attacking Midfielder": attacking_midfielder.ATTACKING_MIDFIELDER_WEIGHTS,
    "Side Midfielder": side_midfielder.SIDE_MIDFIELDER_WEIGHTS,
    "Winger": winger.WINGER_WEIGHTS,
    "Striker": striker.STRIKER_WEIGHTS,
    "Keeper": keeper.KEEPER_WEIGHTS,
}


class PlayerUseCase(IPlayerUseCase):
    def __init__(
        self,
        player_repository: IPlayerRepository,
        game_repository: IGameRepository,
        statistic_repository: IStatisticRepository,
        player_game_statistic_repository: IPlayerGameStatisticRepository
    ):
        self.player_repository = player_repository
        self.game_repository = game_repository
        self.statistic_repository = statistic_repository
        self.player_game_statistic_repository = player_game_statistic_repository

    async def get_info(
        self,
        player_id: int,
    ) -> dict:
        try:
            player_dto = await self.player_repository.get_by_id(player_id)
            stats_dto = await self.statistic_repository.get_by_player_id(player_id)
        except RepositoryConnectionDoesNotExistError:
            raise RepositoryDoesNotExist

        player = player_dto.model_dump()
        stats = stats_dto.model_dump()

        games_dto = await self.game_repository.get_by_player_id(player_id)
        game_ids = [game.id for game in games_dto]
        player_game_statistic_dtos = await self.player_game_statistic_repository.get_for_player_page(
            player_id, game_ids
        )
        player_game_statistics = {
            player_game_statistic.game_id: player_game_statistic.model_dump()
            for player_game_statistic in player_game_statistic_dtos
        }

        games = [
            {
                **game.model_dump(),
                "statistic": player_game_statistics.get(game.id, {})
            }
            for game in games_dto
        ]

        player_ids = [player_dto.id + player_dto.id]

        return {
            **player,
            "stats": stats,
            "games": games,
            "best_positions": await self.get_best_positions(player_id),
            "players_for_compare": await self.player_repository.get_by_ids(player_ids),
        }

    async def get_best_positions(self, player_id: int) -> list[dict[str, float | str]]:
        # Получаем текущего игрока и его статистику
        player_dto = await self.player_repository.get_by_id(player_id)
        player_statistic_dto = await self.statistic_repository.get_by_player_id(player_id)

        # Получаем всех игроков и их статистику
        player_dtos = await self.player_repository.get_all()
        player_ids = [p.id for p in player_dtos]
        player_statistic_dtos = await self.statistic_repository.get_by_player_ids(player_ids)

        # Быстрый доступ к игрокам по ID
        player_by_id = {p.id: p for p in player_dtos}

        # Группы позиций
        attacking_positions = {
            "Striker", "Attacking Midfielder", "Central Midfielder",
            "Right Winger", "Left Winger", "Side Midfielder", "Wide Midfielder", "Winger","Defensive Midfielder","Left Midfielder", "Right Midfielder"
        }

        defensive_positions = {
            "Center Back", "Right Back", "Left Back", "Full Back", "Half-Winger", "Left Wing-Back", "Right Wing-Back", "Keeper"
        }

        # Подстановка эквивалентов для обобщённых позиций
        POSITION_EQUIVALENTS = {
            "Side Midfielder": {"Left Midfielder", "Right Midfielder"},
            "Wide Midfielder": {"Defensive Midfielder", "Central Midfielder"},
            "Full Back": {"Left Back", "Right Back"},
            "Half-Winger": {"Left Wing-Back", "Right Wing-Back"},
            "Winger": {"Left Winger", "Right Winger"}
        }

        # Основная позиция текущего игрока
        main_position = player_dto.position.name if player_dto.position else None

        # Определяем допустимые позиции для оценки
        if main_position in attacking_positions:
            allowed_positions = attacking_positions
        elif main_position in defensive_positions:
            allowed_positions = defensive_positions
        else:
            allowed_positions = set()

        # Считаем лучший балл по каждой позиции
        best_scores = {
            pos: max(
                (self.__calc_score(stat, weights) for stat in player_statistic_dtos),
                default=0
            )
            for pos, weights in POSITION_WEIGHT_MAP.items()
        }

        result = []

        for pos, weights in POSITION_WEIGHT_MAP.items():
            # Пропускаем чуждые позиции
            if pos not in allowed_positions:
                continue

            # Балл текущего игрока на этой позиции
            player_score = self.__calc_score(player_statistic_dto, weights)
            best_score = best_scores[pos]
            percent_of_best = player_score / best_score if best_score else 0

            # Получаем эквивалентные позиции, если есть
            sub_positions = POSITION_EQUIVALENTS.get(pos, {pos})

            # Фильтруем игроков по основной позиции
            filtered_stats = [
                stat for stat in player_statistic_dtos
                if (
                        (player := player_by_id.get(stat.player_id)) and
                        player.position is not None and
                        player.position.name.strip() in sub_positions
                )
            ]

            all_scores = [self.__calc_score(stat, weights) for stat in filtered_stats]
            total = len(all_scores)
            worse_count = sum(1 for s in all_scores if s < player_score)
            relative_percentile = (worse_count / total * 100) if total else 0
            final_probability = round((round(relative_percentile, 2)+round(percent_of_best * 100, 2))/2, 2)

            result.append({
                "position": pos,
                "percent_of_best": round(percent_of_best * 100, 2),
                "players_outperformed_percent": round(relative_percentile, 2),
                "final_score": final_probability,
            })

        result.sort(key=lambda x: x["final_score"], reverse=True)
        return result[:6]

    @staticmethod
    def __calc_score(
            statistic: PlayerStatisticRetrieveDTO,
            weights: dict[str, tuple[int, bool]]
    ) -> int | float:
        score = 0
        for field, weight_info in weights.items():
            weight, is_inverse = weight_info

            if field == "Голевая конверсия":
                value = float(statistic.all_goals/statistic.all_ShotsOnTarget) if statistic.all_ShotsOnTarget != 0 else 0
            elif field == "Минут на гол":
                value = float(statistic.minutes_played // statistic.all_goals) if statistic.all_goals != 0 else 0
            else:
                value = getattr(statistic, field, 0) or 0

            if is_inverse:
                score += float(weight / value) if value != 0 else 0
            else:
                score += float(value) * weight





        return float(score) * (statistic.minutes_played / 2750)
