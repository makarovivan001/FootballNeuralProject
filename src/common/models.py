from django.db import models


class Season(models.Model):
    started_at = models.DateField()
    stopped_at = models.DateField()


class CharacteristicStatus(models.Model):
    name = models.CharField(max_length=63)
    color = models.CharField(max_length=63)
    min_value = models.PositiveSmallIntegerField(default=0)


# class StrengthsAndWeaknesses(models.Model):
#     ...