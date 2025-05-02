from django.db import models

from domain.enums.countries import Country


countries = [(item.value, item.value) for item in Country]


def player_photo_path(instance, filename) -> str:
    return f"players/{filename}"


class Player(models.Model):
    identifier = models.PositiveIntegerField(db_index=True, unique=True)
    club = models.ForeignKey(to="club.Club", on_delete=models.DO_NOTHING, null=True, blank=True)
    photo = models.FileField(upload_to=player_photo_path, default=None, null=True, blank=True)
    photo_url = models.TextField(default=None, null=True, blank=True)
    surname = models.CharField(max_length=63)
    name = models.CharField(max_length=63)
    height = models.PositiveSmallIntegerField(default=0, null=True, blank=True)
    age = models.PositiveSmallIntegerField(default=0, null=True, blank=True)
    country = models.CharField(max_length=63)
    position = models.ManyToManyField(to="Position")
    statistic = models.OneToOneField(to="Statistic", on_delete=models.DO_NOTHING, default=None, null=True)


class Position(models.Model):
    name = models.CharField(max_length=63)


class Statistic(models.Model):
    goals = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, )
    shots = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, )
    ShotsOnTarget = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, )
    assists = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, )
    successful_passes = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, )
    successful_passes_accuracy = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, )
    long_balls_accurate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, )
    long_ball_succeeeded_accuracy = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, )
    chances_created = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, )
    dribbles_succeeded = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, )
    won_contest_subtitle = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, )
    touches = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, )
    touches_opp_box = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, )
    dispossessed = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, )
    fouls_won = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, )
    tackles_succeeded = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, )
    tackles_succeeded_percent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, )
    duel_won = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, )
    duel_won_percent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, )
    aerials_won = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, )
    aerials_won_percent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, )
    interceptions = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, )
    shot_blocked = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, )
    fouls = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, )
    recoveries = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, )
    poss_won_att_3rd_team_title = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, )
    dribbled_past = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, )
    yellow_cards = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, )
    red_cards = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, )