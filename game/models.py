from django.db import models


class Game(models.Model):
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title


class Player(models.Model):
    name = models.CharField(max_length=255)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="players")

    def __str__(self):
        return self.name


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
