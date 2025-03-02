from rest_framework import serializers
from game.models import Game, Player, Task
from collections import defaultdict

import logging 

logger = logging.getLogger("game")

class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = ["id", "name", "game"]


class TaskSerializer(serializers.ModelSerializer):
    completed_by = serializers.StringRelatedField(read_only=True)

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
            "game",
        ]


class GameSerializer(serializers.ModelSerializer):
    players = PlayerSerializer(many=True, read_only=True)
    tasks = serializers.SerializerMethodField()

    class Meta:
        model = Game
        fields = ["id", "title", "players", "tasks"]

    def get_tasks(self, obj):
        # Requires prefetching to have occured before serialization
        tasks = obj.tasks.all()
        grouped_tasks = defaultdict(list)
        for task in tasks:
            grouped_tasks[task.grid_row].append(task)

        return [
            TaskSerializer(grouped_tasks[row], many=True).data
            for row in sorted(grouped_tasks.keys())
        ]
