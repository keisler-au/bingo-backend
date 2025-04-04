import logging
from collections import defaultdict

from rest_framework import serializers

from game.models import Game, Player, Task

logger = logging.getLogger("game")


class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = ["id", "name"]


class TaskSerializer(serializers.ModelSerializer):
    game_id = serializers.IntegerField(source="game.id", read_only=True)
    completed_by = PlayerSerializer(read_only=True)

    class Meta:
        model = Task
        fields = [
            "id",
            "value",
            "grid_row",
            "grid_column",
            "last_updated",
            "completed",
            "completed_by",
            "game_id",
        ]


class GameSerializer(serializers.ModelSerializer):
    players = PlayerSerializer(many=True)
    tasks = serializers.SerializerMethodField()

    class Meta:
        model = Game
        fields = ["id", "code", "title", "players", "tasks"]

    def get_tasks(self, obj):
        tasks = obj.tasks.all().order_by("grid_column")
        grouped_tasks = defaultdict(list)
        for task in tasks:
            grouped_tasks[task.grid_row].append(task)
        return [
            TaskSerializer(grouped_tasks[row], many=True).data
            for row in sorted(grouped_tasks.keys())
        ]
