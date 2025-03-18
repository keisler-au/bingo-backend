import logging

from django.db import IntegrityError, models
from django.utils.crypto import get_random_string

logger = logging.getLogger("game")


class Player(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Game(models.Model):
    code = models.CharField(max_length=6, unique=True, editable=False, default=None)
    title = models.CharField(max_length=255)
    players = models.ManyToManyField(Player, related_name="games")

    @classmethod
    def create_with_unique_code(cls, title):
        """Attempts to create a Game with a unique code, retrying on collision."""
        retry = 100
        while retry:
            try:
                code = get_random_string(
                    6, allowed_chars="ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
                )
                return cls.objects.create(title=title, code=code)
            except IntegrityError:
                retry -= 1
                if not retry:
                    logger.error(
                        f"Failed to generate a unique code after {100} retries"
                    )
                continue


class Task(models.Model):
    value = models.CharField(max_length=255)
    grid_row = models.IntegerField()
    grid_column = models.IntegerField()
    last_updated = models.DateTimeField(auto_now=True)
    completed = models.BooleanField(default=False)
    completed_by = models.ForeignKey(
        Player, null=True, blank=True, on_delete=models.SET_NULL
    )
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="tasks")

    def __str__(self):
        return f"Task {self.id} - {self.value}"
