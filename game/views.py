import json
import logging

from django.db import transaction
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from game.models import Game, Player, Task
from game.serializers import GameSerializer, PlayerSerializer

logger = logging.getLogger("game")


class CreatePlayer(APIView):
    serializer_class = PlayerSerializer

    def post(self, request):
        # TODO: TESTING
        # 1. Unit test
        # 2. If it's not there it will error - Check Django logs
        try:
            player_name = request.data.get("data")
            player = Player.objects.create(name=player_name)
            serializer = self.serializer_class(player)
            response = Response(
                {"status": "success", "player": serializer.data}, status=200
            )
        except Exception as e:
            logger.exception("Unexpected error creating player:", exc_info=e)
            response = Response(
                {"status": "error", "message": "Unexpected Error"}, status=500
            )

        return response


class CreateAndRetrieveGame(APIView):
    serializer_class = GameSerializer

    def post(self, request):
        # TODO: TESTING
        # Unit test
        # Logging - Error gets sent back to frontend and modal already displayed
        try:
            game = request.data.get("data")
            player_id = game.get("player_id")
            title = game.get("title")
            game_values = game.get("values")

            tasks_to_create = []
            with transaction.atomic():
                created_game = Game.create_with_unique_code(title)
                player = Player.objects.get(id=player_id)
                created_game.players.add(player)
                for rowIndex, row in enumerate(game_values):
                    for colIndex, value in enumerate(row):
                        task = Task(
                            value=value,
                            grid_row=rowIndex,
                            grid_column=colIndex,
                            game=created_game,
                        )
                        tasks_to_create.append(task)
                Task.objects.bulk_create(tasks_to_create)

            game = (
                Game.objects.filter(id=created_game.id)
                .prefetch_related("tasks", "players")
                .first()
            )
            serializer = self.serializer_class(game)
            response = Response(
                {"status": "success", "game": serializer.data}, status=200
            )
        except Exception as e:
            logger.exception("Unexpected Error: ", exc_info=e)
            response = Response(
                {"status": "error", "message": "Unexpected Error"}, status=500
            )

        return response


class RetrieveGame(APIView):
    serializer_class = GameSerializer

    def post(self, request):
        response = Response(
            {"status": "error", "message": "Game not found or game has no players"},
            status=404,
        )
        # TODO: TESTING
        # 1. Unit test
        # 2. Won't be able to enter the game
        try:
            data = request.data.get("data")
            game_code = data.get("code")
            player_id = data.get("player").get("id")
            game = (
                Game.objects.filter(code=game_code)
                .prefetch_related("tasks", "players")
                .first()
            )
            if game:
                player = Player.objects.get(id=player_id)
                game.players.add(player)
                serializer = self.serializer_class(game)
                response = Response(
                    {"status": "success", "game": serializer.data}, status=200
                )
        except Exception as e:
            logger.exception("Unexpected Error: ", exc_info=e)
            response = Response(
                {"status": "error", "message": "Unexpected Error"}, status=500
            )

        return response
