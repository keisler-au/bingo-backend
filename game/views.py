import json
import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from game.models import Game, Task
from game.serializers import GameSerializer

logger = logging.getLogger("game")


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
