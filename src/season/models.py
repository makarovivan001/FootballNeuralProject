from django.db import models


class Season(models.Model):
    name = models.CharField(max_length=15)
    club_ids = models.JSONField(default=list)

    class Meta:
        db_table = "season"
        ordering = ["-id"]