from django.test import TestCase

# TODO: TESTING


# from django.test import TestCase
# from game.models import Game
# from game.serializers import GameSerializer

# class GameSerializerTest(TestCase):
#     def test_prefetch_related_reduces_queries(self):
#         # Set up data
#         game = Game.objects.create(title="Test Game")
#         game.tasks.create(value="Task 1", grid_row=1, grid_column=1)
#         game.tasks.create(value="Task 2", grid_row=1, grid_column=2)

#         # Prefetch related tasks
#         with self.assertNumQueries(2):  # One for the games and one for the tasks
#             games = Game.objects.prefetch_related('tasks').all()
#             serialized_data = GameSerializer(games, many=True).data
