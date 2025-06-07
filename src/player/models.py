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
    number = models.PositiveSmallIntegerField(default=0, null=True, blank=True)
    country = models.CharField(max_length=63)
    role_ids = models.JSONField(default=list)
    position = models.ForeignKey("player.Position", on_delete=models.DO_NOTHING, null=True, blank=True)
    statistic = models.OneToOneField(to="PlayerStatistic", on_delete=models.DO_NOTHING, related_name="player", default=None, null=True)
    preferred_foot = models.CharField(max_length=63, default=None, null=True, blank=True)


class Position(models.Model):
    name = models.CharField(max_length=63)


class Role(models.Model):
    name = models.CharField(max_length=63)


class PlayerStatistic(models.Model):
    all_goals = models.PositiveIntegerField(default=0, blank=True)
    all_ShotsOnTarget = models.PositiveIntegerField(default=0, blank=True)
    all_yellow_cards = models.PositiveIntegerField(default=0, blank=True)
    all_red_cards = models.PositiveIntegerField(default=0, blank=True)
    all_assists = models.PositiveIntegerField(default=0, blank=True)
    all_chances_created = models.PositiveIntegerField(default=0, blank=True)
    all_dribbles_succeeded = models.PositiveIntegerField(default=0, blank=True)
    all_dispossessed = models.PositiveIntegerField(default=0, blank=True)

    # Вышел в стартовом составе
    started = models.PositiveSmallIntegerField(default=0, blank=True)
    # Всего матчей
    matches_uppercase = models.PositiveSmallIntegerField(default=0, blank=True)
    minutes_played = models.PositiveIntegerField(default=0, blank=True)
    rating = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    goals = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    shots = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    ShotsOnTarget = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    assists = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    successful_passes = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    successful_passes_accuracy = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    long_balls_accurate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    long_ball_succeeeded_accuracy = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    chances_created = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    dribbles_succeeded = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    won_contest_subtitle = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    touches = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    touches_opp_box = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    dispossessed = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    fouls_won = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    tackles_succeeded = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    tackles_succeeded_percent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    duel_won = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    duel_won_percent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    aerials_won = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    aerials_won_percent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    interceptions = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    shot_blocked = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    fouls = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    recoveries = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    poss_won_att_3rd_team_title = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    dribbled_past = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    yellow_cards = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    red_cards = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    crosses_succeeeded = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    crosses_succeeeded_accuracy = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    # TODO: перенести сюда player_id и доавить сезоны. Новый сезон - новая запись

    # Часть для вратарей
    saves = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    save_percentage = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    goals_conceded = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    clean_sheet_team_title = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    penalties_faced = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    penalty_goals_conceded = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    penalty_saves = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    error_led_to_goal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    keeper_sweeper = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    keeper_high_claim = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)

    class Meta:
        db_table = "player_statistic"


class PlayerGameStatistic(models.Model):
    game = models.ForeignKey(to="game.Game", on_delete=models.CASCADE)
    player = models.ForeignKey(to="Player", on_delete=models.CASCADE)
    rating_title = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    minutes_played = models.IntegerField(default=0, blank=True)
    goals = models.IntegerField(default=0, blank=True)
    assists = models.IntegerField(default=0, blank=True)
    total_shots = models.IntegerField(default=0, blank=True)
    accurate_passes = models.CharField(max_length=15)
    chances_created = models.IntegerField(default=0, blank=True)
    touches = models.IntegerField(default=0, blank=True)
    touches_opp_box = models.IntegerField(default=0, blank=True)
    passes_into_final_third = models.IntegerField(default=0, blank=True)
    accurate_crosses = models.CharField(max_length=15)
    long_balls_accurate = models.CharField(max_length=15)
    corners = models.IntegerField(default=0, blank=True)
    dispossessed = models.IntegerField(default=0, blank=True)
    tackles_succeeded = models.CharField(max_length=15)
    clearances = models.IntegerField(default=0, blank=True)
    headed_clearance = models.IntegerField(default=0, blank=True)
    interceptions = models.IntegerField(default=0, blank=True)
    defensive_actions = models.IntegerField(default=0, blank=True)
    recoveries = models.IntegerField(default=0, blank=True)
    dribbled_past = models.IntegerField(default=0, blank=True)
    duel_won = models.IntegerField(default=0, blank=True)
    duel_lost = models.IntegerField(default=0, blank=True)
    ground_duels_won = models.CharField(max_length=15)
    aerials_won = models.CharField(max_length=15)
    was_fouled = models.IntegerField(default=0, blank=True)
    fouls = models.IntegerField(default=0, blank=True)

    saves = models.IntegerField(default=0, blank=True)
    goals_conceded = models.IntegerField(default=0, blank=True)
    keeper_diving_save = models.IntegerField(default=0, blank=True)
    saves_inside_box = models.IntegerField(default=0, blank=True)
    keeper_sweeper = models.IntegerField(default=0, blank=True)
    punches = models.IntegerField(default=0, blank=True)
    player_throws = models.IntegerField(default=0, blank=True)
    keeper_high_claim = models.IntegerField(default=0, blank=True)

    class Meta:
        db_table = "player_game_statistic"