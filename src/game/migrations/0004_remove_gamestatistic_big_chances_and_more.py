# Generated by Django 5.0.7 on 2025-05-28 14:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0003_game_season_game_tour'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='gamestatistic',
            name='big_chances',
        ),
        migrations.RemoveField(
            model_name='gamestatistic',
            name='big_chances_missed',
        ),
        migrations.RemoveField(
            model_name='gamestatistic',
            name='goal_attempts',
        ),
        migrations.RemoveField(
            model_name='gamestatistic',
            name='possession',
        ),
        migrations.RemoveField(
            model_name='gamestatistic',
            name='saves',
        ),
        migrations.RemoveField(
            model_name='gamestatistic',
            name='shots',
        ),
        migrations.RemoveField(
            model_name='gamestatistic',
            name='tackles',
        ),
        migrations.RemoveField(
            model_name='gamestatistic',
            name='xg',
        ),
        migrations.AddField(
            model_name='gamestatistic',
            name='accurate_crosses',
            field=models.PositiveSmallIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='gamestatistic',
            name='accurate_crosses_persent',
            field=models.PositiveSmallIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='gamestatistic',
            name='accurate_passes',
            field=models.PositiveSmallIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='gamestatistic',
            name='accurate_passes_persent',
            field=models.PositiveSmallIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='gamestatistic',
            name='aerials_won',
            field=models.PositiveSmallIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='gamestatistic',
            name='aerials_won_persent',
            field=models.PositiveSmallIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='gamestatistic',
            name='big_chance',
            field=models.PositiveSmallIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='gamestatistic',
            name='big_chance_missed_title',
            field=models.PositiveSmallIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='gamestatistic',
            name='clearances',
            field=models.PositiveSmallIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='gamestatistic',
            name='dribbles_succeeded',
            field=models.PositiveSmallIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='gamestatistic',
            name='dribbles_succeeded_persent',
            field=models.PositiveSmallIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='gamestatistic',
            name='duel_won',
            field=models.PositiveSmallIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='gamestatistic',
            name='ground_duels_won',
            field=models.PositiveSmallIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='gamestatistic',
            name='ground_duels_won_persent',
            field=models.PositiveSmallIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='gamestatistic',
            name='interceptions',
            field=models.PositiveSmallIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='gamestatistic',
            name='keeper_saves',
            field=models.PositiveSmallIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='gamestatistic',
            name='long_balls_accurate',
            field=models.PositiveSmallIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='gamestatistic',
            name='long_balls_accurate_persent',
            field=models.PositiveSmallIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='gamestatistic',
            name='opposition_half_passes',
            field=models.PositiveSmallIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='gamestatistic',
            name='own_half_passes',
            field=models.PositiveSmallIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='gamestatistic',
            name='player_throws',
            field=models.PositiveSmallIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='gamestatistic',
            name='shot_blocks',
            field=models.PositiveSmallIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='gamestatistic',
            name='shots_woodwork',
            field=models.PositiveSmallIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='gamestatistic',
            name='tackles_succeeded',
            field=models.PositiveSmallIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='gamestatistic',
            name='tackles_succeeded_persent',
            field=models.PositiveSmallIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='gamestatistic',
            name='total_shots',
            field=models.PositiveSmallIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='gamestatistic',
            name='touches_opp_box',
            field=models.PositiveSmallIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='history',
            name='overload_minutes',
            field=models.PositiveSmallIntegerField(default=None, null=True),
        ),
        migrations.AddField(
            model_name='history',
            name='swap',
            field=models.JSONField(default=list, null=True),
        ),
        migrations.AlterField(
            model_name='gamestatistic',
            name='blocked_shots',
            field=models.PositiveSmallIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='gamestatistic',
            name='corners',
            field=models.PositiveSmallIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='gamestatistic',
            name='fouls',
            field=models.PositiveSmallIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='gamestatistic',
            name='offsides',
            field=models.PositiveSmallIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='gamestatistic',
            name='passes',
            field=models.PositiveSmallIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='gamestatistic',
            name='red_cards',
            field=models.PositiveSmallIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='gamestatistic',
            name='shots_inside_box',
            field=models.PositiveSmallIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='gamestatistic',
            name='shots_off_target',
            field=models.PositiveSmallIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='gamestatistic',
            name='shots_on_target',
            field=models.PositiveSmallIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='gamestatistic',
            name='shots_outside_box',
            field=models.PositiveSmallIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='gamestatistic',
            name='yellow_cards',
            field=models.PositiveSmallIntegerField(blank=True, default=None, null=True),
        ),
    ]
