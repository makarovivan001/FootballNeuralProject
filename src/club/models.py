from django.db import models


class Club(models.Model):
    identifier = models.PositiveIntegerField(db_index=True, unique=True)
    name = models.CharField(max_length=63)
    photo = models.FileField(upload_to=".../media/clubs", default=None, null=True, blank=True)
    photo_url = models.TextField(default=None, null=True, blank=True)
    stadium_name = models.CharField(max_length=63)
    stadium_count_of_sits = models.PositiveIntegerField(default=0)
    city_name = models.CharField(max_length=63)
    # расстановка команды на поле
    placement = models.JSONField(default=dict)

# TODO: Добавить таблицу с сезон-клуб-очки
# (можно добавить поле позиция в рейтиге но наверное не надо)
# Очки высчитываются за (победу +3/ничью +1/поражение +0)
# Оно нужно для сортировки в таблице рейтинга(турнирнаая таблица)