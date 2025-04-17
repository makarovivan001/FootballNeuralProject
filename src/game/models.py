from django.db import models
from django.db.models import PositiveSmallIntegerField

from domain.enums.game_history_action import GameHistoryAction

action = [(item.value, item.value) for item in GameHistoryAction]


class Game(models.Model):
    identifier = models.PositiveSmallIntegerField(db_index=True, unique=True)
    game_date = models.DateTimeField()
    is_finished = models.BooleanField(default=False)
    home_club = models.ForeignKey(to="club.Club", on_delete=models.DO_NOTHING, related_name="home_club")
    away_club = models.ForeignKey(to="club.Club", on_delete=models.DO_NOTHING, related_name="away_club")
    best_player = models.ForeignKey(to="player.Player", on_delete=models.DO_NOTHING, default=None, blank=True)
    home_score = PositiveSmallIntegerField(default=0, blank=True)
    away_score = PositiveSmallIntegerField(default=0, blank=True)
    home_club_placement = models.JSONField(default=dict)
    away_club_placement = models.JSONField(default=dict)


class Statictic(models.Model):
    club = models.ForeignKey(to="club.Club", on_delete=models.DO_NOTHING)
    game = models.ForeignKey(to="Game", on_delete=models.DO_NOTHING)
    xg = models.DecimalField(decimal_places=2, max_digits=5, default=0.00)
    goal_attempts = models.PositiveSmallIntegerField(default=0)
    shots = models.PositiveSmallIntegerField(default=0)
    saves = models.PositiveSmallIntegerField(default=0)
    corners = models.PositiveSmallIntegerField(default=0)
    fouls = models.PositiveSmallIntegerField(default=0)
    passes = models.PositiveSmallIntegerField(default=0)
    tackles = models.PositiveSmallIntegerField(default=0)
    yellow_cards = models.PositiveSmallIntegerField(default=0)
    red_cards = models.PositiveSmallIntegerField(default=0)
    shots_on_target = models.PositiveSmallIntegerField(default=0)
    shots_off_target = models.PositiveSmallIntegerField(default=0)
    blocked_shots = models.PositiveSmallIntegerField(default=0)
    shots_inside_box = models.PositiveSmallIntegerField(default=0)
    shots_outside_box = models.PositiveSmallIntegerField(default=0)
    big_chances_missed = models.PositiveSmallIntegerField(default=0)
    offsides = models.PositiveSmallIntegerField(default=0)
    possession = models.DecimalField(decimal_places=2, max_digits=5, default=0.00)
    big_chances = models.PositiveSmallIntegerField(default=0)


class History(models.Model):
    game_id = models.ForeignKey(to="Game", on_delete=models.DO_NOTHING)
    player = models.ForeignKey(to="player.Player", on_delete=models.DO_NOTHING)
    action = models.CharField(max_length=63, choices=action)
    minutes = models.PositiveSmallIntegerField(default=0)