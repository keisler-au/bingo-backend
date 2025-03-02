import json
import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from game.models import Game, Task
from game.serializers import GameSerializer

logger = logging.getLogger("game")

# Create Serializers (for both incoming and outgoing data)
# incoming - serializer.valid()
# outgoing - serialized_tasks = TaskSerializer(tasks, many=True).data
# Create helper function that collates and serializers the game data
# Both Publish and Play need to recieve this formatted data because Play will be built to recieve it when getting updates during play - which is neccessary
# Then update Play.tsx to use the new data
# Then test it
# Then update Join.tsx to also post and then route to Play.tsx
# And then review, consolidate, and test it thoroughly before moving on
# The next phase after this is Players
# And then push and pull baby
# And then profile page
# And then feedback page

# HELPER_FUNCTION(game_id)
# game = (
#     Game.objects.filter(id=game_id)
#     .prefetch_related("tasks")
#     .order_by('grid_row', 'grid_column')
#     .first()
# )
# max_row = game.tasks.aggregate(Max('grid_row'))['grid_row__max']
# max_col = game.tasks.aggregate(Max('grid_column'))['grid_column__max']

# grid = [[None] * (max_col + 1) for _ in range(max_row + 1)]
# tasks = Task.objects.filter(game=game)
# serialized_tasks = TaskSerializer(tasks, many=True).data

# for task in serialized_tasks:
#     grid[task['grid_row']][task['grid_column']] = task

# return grid


class CreateAndRetrieveGame(APIView):
    serializer_class = GameSerializer

    def post(self, request):
        try:
            game = request.data.get("game")
            title = game.get("title")
            game_values = game.get("values")
            # Create game
            tasks_to_create = []
            with transaction.atomic():
                createdGame = Game.objects.create(title=title)
                for rowIndex, row in enumerate(game_values):
                    for colIndex, value in enumerate(row):
                        task = Task(
                            value=value,
                            grid_row=rowIndex,
                            grid_column=colIndex,
                            game=createdGame,
                        )
                        tasks_to_create.append(task)
                Task.objects.bulk_create(tasks_to_create)
            # Retrieve game
            game = (
                Game.objects.filter(id=createdGame.id)
                .prefetch_related("tasks", "players")
                # .order_by("tasks__row_index", "tasks__col_index")
                .first()
            )

            serializer = self.serializer_class(game)
            response = Response(
                {"status": "success", "game": serializer.data}, status=200
            )
        except Exception as e:
            logger.error("Unexpected Error: ", str(e))
            response = Response(
                {"status": "error", "message": "Unexpected Error"}, status=500
            )

        return response


class RetrieveGame(GenericAPIView):
    serializer_class = GameSerializer

    def get_queryset(self):
        game_id = self.request.data.get("game")
        return (
            Game.objects.filter(id=game_id)
            .prefetch_related("tasks", "players")
            # .order_by("tasks__row_index", "tasks__col_index")
        )

    def post(self, request):
        try:
            game = self.get_object()
            serializer = self.serializer_class(game)
            response = Response(
                {"status": "success", "game": serializer.data}, status=200
            )
        except Exception as e:
            logger.error("Unexpected Error: ", str(e))
            response = Response(
                {"status": "error", "message": "Unexpected Error"}, status=500
            )

        return response
