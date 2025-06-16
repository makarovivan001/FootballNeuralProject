from django.db import models

from season.models import Season


class Game(models.Model):
    identifier = models.PositiveIntegerField(db_index=True, unique=True)
    game_date = models.DateTimeField()
    is_finished = models.BooleanField(default=False)
    home_club = models.ForeignKey(to="club.Club", on_delete=models.DO_NOTHING, related_name="home_club")
    away_club = models.ForeignKey(to="club.Club", on_delete=models.DO_NOTHING, related_name="away_club")
    best_player = models.ForeignKey(to="player.Player", on_delete=models.DO_NOTHING, default=None, null=True, blank=True)
    home_score = models.PositiveSmallIntegerField(default=0, blank=True)
    away_score = models.PositiveSmallIntegerField(default=0, blank=True)
    home_club_placement = models.JSONField(default=list)
    away_club_placement = models.JSONField(default=list)
    home_players = models.JSONField(default=list)
    away_players = models.JSONField(default=list)
    season = models.ForeignKey(to=Season, on_delete=models.CASCADE, related_name="games", null=True, default=None)
    tour = models.PositiveSmallIntegerField(default=0)


class GameStatistic(models.Model):
    club = models.ForeignKey(to="club.Club", on_delete=models.DO_NOTHING)
    game = models.ForeignKey(to="Game", on_delete=models.DO_NOTHING)
    big_chance = models.PositiveSmallIntegerField(default=None, blank=True, null=True)
    big_chance_missed_title = models.PositiveSmallIntegerField(default=None, blank=True, null=True)
    fouls = models.PositiveSmallIntegerField(default=None, blank=True, null=True)
    corners = models.PositiveSmallIntegerField(default=None, blank=True, null=True)
    total_shots = models.PositiveSmallIntegerField(default=None, blank=True, null=True)
    shots_on_target = models.PositiveSmallIntegerField(default=None, blank=True, null=True)
    shots_off_target = models.PositiveSmallIntegerField(default=None, blank=True, null=True)
    blocked_shots = models.PositiveSmallIntegerField(default=None, blank=True, null=True)
    shots_woodwork = models.PositiveSmallIntegerField(default=None, blank=True, null=True)
    shots_inside_box = models.PositiveSmallIntegerField(default=None, blank=True, null=True)
    shots_outside_box = models.PositiveSmallIntegerField(default=None, blank=True, null=True)
    passes = models.PositiveSmallIntegerField(default=None, blank=True, null=True)
    accurate_passes = models.PositiveSmallIntegerField(default=None, blank=True, null=True)
    accurate_passes_persent = models.PositiveSmallIntegerField(default=None, blank=True, null=True)
    own_half_passes = models.PositiveSmallIntegerField(default=None, blank=True, null=True)
    opposition_half_passes = models.PositiveSmallIntegerField(default=None, blank=True, null=True)
    long_balls_accurate = models.PositiveSmallIntegerField(default=None, blank=True, null=True)
    long_balls_accurate_persent = models.PositiveSmallIntegerField(default=None, blank=True, null=True)
    accurate_crosses = models.PositiveSmallIntegerField(default=None, blank=True, null=True)
    accurate_crosses_persent = models.PositiveSmallIntegerField(default=None, blank=True, null=True)
    player_throws = models.PositiveSmallIntegerField(default=None, blank=True, null=True)
    touches_opp_box = models.PositiveSmallIntegerField(default=None, blank=True, null=True)
    offsides = models.PositiveSmallIntegerField(default=None, blank=True, null=True)
    tackles_succeeded = models.PositiveSmallIntegerField(default=None, blank=True, null=True)
    tackles_succeeded_persent = models.PositiveSmallIntegerField(default=None, blank=True, null=True)
    interceptions = models.PositiveSmallIntegerField(default=None, blank=True, null=True)
    shot_blocks = models.PositiveSmallIntegerField(default=None, blank=True, null=True)
    clearances = models.PositiveSmallIntegerField(default=None, blank=True, null=True)
    keeper_saves = models.PositiveSmallIntegerField(default=None, blank=True, null=True)
    duel_won = models.PositiveSmallIntegerField(default=None, blank=True, null=True)
    ground_duels_won = models.PositiveSmallIntegerField(default=None, blank=True, null=True)
    ground_duels_won_persent = models.PositiveSmallIntegerField(default=None, blank=True, null=True)
    aerials_won = models.PositiveSmallIntegerField(default=None, blank=True, null=True)
    aerials_won_persent = models.PositiveSmallIntegerField(default=None, blank=True, null=True)
    dribbles_succeeded = models.PositiveSmallIntegerField(default=None, blank=True, null=True)
    dribbles_succeeded_persent = models.PositiveSmallIntegerField(default=None, blank=True, null=True)
    yellow_cards = models.PositiveSmallIntegerField(default=None, blank=True, null=True)
    red_cards = models.PositiveSmallIntegerField(default=None, blank=True, null=True)


class History(models.Model):
    game = models.ForeignKey(to="Game", on_delete=models.DO_NOTHING)
    player = models.ForeignKey(to="player.Player", on_delete=models.DO_NOTHING, null=True)
    is_home = models.BooleanField(default=True)
    action = models.ForeignKey("Action", on_delete=models.DO_NOTHING)
    minutes = models.PositiveSmallIntegerField(default=0)
    overload_minutes = models.PositiveSmallIntegerField(default=None, null=True)
    swap = models.JSONField(default=list, null=True)


class Action(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        db_table = "action"
