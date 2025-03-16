from django.test import TestCase
from game.models import Game
from game.serializers import GameSerializer

class GameSerializerTest(TestCase):
    def test_prefetch_related_reduces_queries(self):
        # Set up data
        game = Game.objects.create(title="Test Game", code="123456")
        game.tasks.create(value="Task 1", grid_row=1, grid_column=1)
        game.tasks.create(value="Task 2", grid_row=1, grid_column=2)

        # Prefetch related tasks
        with self.assertNumQueries(3):
            games = Game.objects.prefetch_related("players", 'tasks').order_by("tasks__grid_column").all()
            GameSerializer(games, many=True).data
