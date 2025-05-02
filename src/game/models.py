from django.db import models

from domain.enums.game_history_action import GameHistoryAction


action = [(item.value, item.value) for item in GameHistoryAction]


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


class Statistic(models.Model):
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
    game = models.ForeignKey(to="Game", on_delete=models.DO_NOTHING)
    is_home_club = models.BooleanField(default=True)
    player = models.ForeignKey(to="player.Player", on_delete=models.DO_NOTHING)
    action = models.ForeignKey("Action", on_delete=models.DO_NOTHING)
    minutes = models.PositiveSmallIntegerField(default=0)


class Action(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        db_table = "action"

"""
"Card",
"Goal",
"Assist",
"MissedPenalty",
"Half",
"Substitution",
"Yellow",
"YellowRed",
"Injuries",
"InternationalDuty"

"""