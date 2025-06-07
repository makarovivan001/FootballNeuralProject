from collections import defaultdict
from functools import cmp_to_key

from adrf.requests import AsyncRequest

from domain.exceptions.repositories.main import RepositoryConnectionDoesNotExistError
from domain.exceptions.use_cases.common import RepositoryDoesNotExist
from domain.interfaces.repositories.club.main import IClubRepository
from domain.interfaces.repositories.game.main import IGameRepository
from domain.interfaces.repositories.player.main import IPlayerRepository
from domain.interfaces.repositories.season.main import ISeasonRepository
from domain.interfaces.use_cases.club.main import IClubUseCase


class ClubUseCase(IClubUseCase):
    def __init__(
            self,
            club_repository: IClubRepository,
            game_repository: IGameRepository,
            player_repository: IPlayerRepository,
            season_repository: ISeasonRepository,
    ):
        self.club_repository = club_repository
        self.game_repository = game_repository
        self.player_repository = player_repository
        self.season_repository = season_repository

    async def get_all(
            self,
    ) -> dict:
        last_season_id = await self.season_repository.get_last()
        club_dto_list = await self.club_repository.get_by_season_id(last_season_id)

        club_list = [
            club_dto.model_dump()
            for club_dto in club_dto_list
        ]

        game_list = await self.game_repository.get_near_games()
        games_of_season = await self.game_repository.get_by_season_id(last_season_id)

        tournament_table = {}
        for game in games_of_season:
            home_win = 0
            away_win = 0
            home_win_count = 0
            away_win_count = 0
            if game.home_score > game.away_score:
                home_win = 3
                home_win_count = 1
            elif game.home_score == game.away_score:
                home_win = 1
                away_win = 1
            else:
                away_win = 3
                away_win_count = 1

            home_wins = {}
            away_wins = {}
            if home_win_count:
                home_wins[game.away_club.id] = {
                    'win_count': 1,
                    'goals': game.home_score
                }
            elif away_win_count:
                away_wins[game.home_club.id] = {
                    'win_count': 1,
                    'goals': game.away_score
                }

            self.__set_game_info(
                tournament_table=tournament_table,
                club_id=game.home_club.id,
                win_score=home_win,
                is_win=home_win_count,
                club_score=game.home_score,
                opponent_score=game.away_score,
                wins=home_wins,
            )
            self.__set_game_info(
                tournament_table=tournament_table,
                club_id=game.away_club.id,
                win_score=away_win,
                is_win=away_win_count,
                club_score=game.away_score,
                opponent_score=game.home_score,
                wins=away_wins,
            )

        sorted_clubs = self.__get_sorted_team_table(tournament_table)
        clubs = await self.club_repository.get_sorted_clubs(
            [club['club_id'] for club in sorted_clubs   ]
        )

        for club in sorted_clubs:
            club['club'] = clubs[club['club_id']].model_dump()

        return {
            'clubs': club_list,
            'games': game_list,
            'tournament_table': sorted_clubs
        }



    def __set_game_info(
            self,
            tournament_table: dict,
            club_id: int,
            win_score: int,
            is_win: int,
            club_score: int,
            opponent_score: int,
            wins: dict,
    ) -> None:
        if tournament_table.get(club_id, False):
            tournament_table[club_id]['table_score'] += win_score
            tournament_table[club_id]['missed_goals'] += opponent_score
            tournament_table[club_id]['goals'] += club_score
            tournament_table[club_id]['win_count'] += is_win
            tournament_table[club_id]['game_count'] += 1
            tournament_table[club_id]['draw_game_count'] += 1 if win_score == 1 else 0
            tournament_table[club_id]['lose_game_count'] += 1 if win_score == 0 else 0


            try:
                opponent_id = list(wins)[0]
                if tournament_table[club_id]['wins'].get(opponent_id, False):
                    tournament_table[club_id]['wins'][opponent_id]['win_count'] += wins[opponent_id]['win_count']
                    tournament_table[club_id]['wins'][opponent_id]['goals'] += wins[opponent_id]['goals']
                else:
                    tournament_table[club_id]['wins'].update(wins)
            except: pass
        else:
            tournament_table[club_id] = {
                'wins': wins,
                'table_score': win_score,
                'missed_goals': opponent_score,
                'goals': club_score,
                'win_count': is_win,
                'game_count': 1,
                'draw_game_count': 1 if win_score == 1 else 0,
                'lose_game_count': 1 if win_score == 0 else 0,
            }



    async def get_page_info(
            self,
            request: AsyncRequest,
            club_id: int
    ) -> dict:
        try:
            club_dto = await self.club_repository.get_club_info(club_id)

        except RepositoryConnectionDoesNotExistError:
            raise RepositoryDoesNotExist
        club = club_dto.model_dump()

        games_dto = await self.game_repository.get_by_club_id(
            club_id=club_id,
        )

        games = [
            game.model_dump()
            for game in games_dto
        ]

        players_dto = await self.player_repository.get_by_club_id(
            club_id=club_id,
        )

        players = [
            player.model_dump()
            for player in players_dto
        ]

        return {
            "club": club,
            "games": games,
            "players": players
        }

    def __parse_teams_data(self, data: dict) -> dict:
        teams = {}

        for team_id, team_data in data.items():
            teams[team_id] = {
                'id': team_id,
                'points': team_data['table_score'],
                'wins': team_data['win_count'],
                'goals': team_data['goals'],
                'missed': team_data['missed_goals'],
                'diff': team_data['goals'] - team_data['missed_goals'],
                'vs': defaultdict(lambda: {'goals_for': 0, 'goals_against': 0, 'wins': 0}),
                'game_count': team_data['game_count'],
                'draw_game_count': team_data['draw_game_count'],
                'lose_game_count': team_data['lose_game_count'],
            }

        for team_id, team_data in data.items():
            for opponent_id, result in team_data.get('wins', {}).items():
                teams[team_id]['vs'][opponent_id]['goals_for'] += result['goals']
                teams[team_id]['vs'][opponent_id]['wins'] += result['win_count']
                teams[opponent_id]['vs'][team_id]['goals_against'] += result['goals']

        return teams

    def __compare_teams(self, a, b, teams) -> int:
        if teams[a]['points'] != teams[b]['points']:
            return teams[b]['points'] - teams[a]['points']

        a_vs_b = teams[a]['vs'][b]
        b_vs_a = teams[b]['vs'][a]

        if a_vs_b['wins'] != b_vs_a['wins']:
            return b_vs_a['wins'] - a_vs_b['wins']

        a_diff = a_vs_b['goals_for'] - a_vs_b['goals_against']
        b_diff = b_vs_a['goals_for'] - b_vs_a['goals_against']
        if a_diff != b_diff:
            return b_diff - a_diff

        if teams[a]['wins'] != teams[b]['wins']:
            return teams[b]['wins'] - teams[a]['wins']

        if teams[a]['diff'] != teams[b]['diff']:
            return teams[b]['diff'] - teams[a]['diff']

        return 0

    def __get_sorted_team_table(self, data: dict) -> list:
        teams = self.__parse_teams_data(data)
        sorted_ids = sorted(teams.keys(), key=cmp_to_key(lambda a, b: self.__compare_teams(a, b, teams)))
        table = []

        for rank, club_id in enumerate(sorted_ids, 1):
            team = teams[club_id]
            table.append({
                'place': rank,
                'club_id': club_id,
                'points': team['points'],
                'wins': team['wins'],
                'goals_scored': team['goals'],
                'goals_missed': team['missed'],
                'goal_difference': team['diff'],
                'game_count': team['game_count'],
                'draw_game_count': team['draw_game_count'],
                'lose_game_count': team['lose_game_count'],
            })

        return table