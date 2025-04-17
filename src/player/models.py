from django.db import models

from domain.enums.countries import Country

countries = [(item.value, item.value) for item in Country]

def player_photo_path(instance, filename) -> str:
    return f"players/{filename}"

class Player(models.Model):
    identifier = models.PositiveSmallIntegerField(db_index=True, unique=True)
    club = models.ForeignKey(to="club.Club", on_delete=models.DO_NOTHING)
    photo = models.FileField(upload_to=player_photo_path)
    surname = models.CharField(max_length=63)
    name = models.CharField(max_length=63)
    height = models.PositiveSmallIntegerField(default=0)
    age = models.PositiveSmallIntegerField(default=0)
    country = models.CharField(max_length=63, choices=countries)
    position = models.ManyToManyField(to="Position")


class Position(models.Model):
    name =  models.CharField(max_length=63)


class Statistic(models.Model):
    rating_title = models.DecimalField(max_digits=3, decimal_places=2)
    minutes_played = models.PositiveSmallIntegerField(default=0)
    goals = models.PositiveSmallIntegerField(default=0)
    assists = models.PositiveSmallIntegerField(default=0)
    total_shots = models.PositiveSmallIntegerField(default=0)
    all_passes = models.PositiveSmallIntegerField(default=0)
    accurate_passes = models.PositiveSmallIntegerField(default=0)
    chances_created = models.PositiveSmallIntegerField(default=0)
    all_shots = models.PositiveSmallIntegerField(default=0)
    shotsOnTarget = models.PositiveSmallIntegerField(default=0)
    touches = models.PositiveSmallIntegerField(default=0)
    touches_opp_box = models.PositiveSmallIntegerField(default=0)
    passes_into_final_third = models.PositiveSmallIntegerField(default=0)
    all_crosses = models.PositiveSmallIntegerField(default=0)
    accurate_crosses = models.PositiveSmallIntegerField(default=0)
    all_long_balls = models.PositiveSmallIntegerField(default=0)
    accurate_long_balls = models.PositiveSmallIntegerField(default=0)
    corners = models.PositiveSmallIntegerField(default=0)
    dispossessed = models.PositiveSmallIntegerField(default=0)
    all_tackles = models.PositiveSmallIntegerField(default=0)
    success_tackles = models.PositiveSmallIntegerField(default=0)
    clearances = models.PositiveSmallIntegerField(default=0)
    interceptions = models.PositiveSmallIntegerField(default=0)
    defensive_actions = models.PositiveSmallIntegerField(default=0)
    recoveries = models.PositiveSmallIntegerField(default=0)
    dribbled_past = models.PositiveSmallIntegerField(default=0)
    duel_won = models.PositiveSmallIntegerField(default=0)
    duel_lost = models.PositiveSmallIntegerField(default=0)
    ground_duels = models.PositiveSmallIntegerField(default=0)
    success_ground_duels = models.PositiveSmallIntegerField(default=0)
    aerials = models.PositiveSmallIntegerField(default=0)
    success_aerials = models.PositiveSmallIntegerField(default=0)
    was_fouled = models.PositiveSmallIntegerField(default=0)
    fouls = models.PositiveSmallIntegerField(default=0)


