import json
import logging

import sentry_sdk
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
        try:
            player_name = request.data
            player = Player.objects.create(name=player_name)
            serializer = self.serializer_class(player)
            response = Response(
                {"status": "success", "player": serializer.data}, status=200
            )
        except Exception as e:
            logger.exception("Unexpected error creating player:", exc_info=e)
            sentry_sdk.capture_exception(e)
            response = Response(
                {"status": "error", "message": "Unexpected Error"}, status=500
            )

        return response


class CreateAndRetrieveGame(APIView):
    serializer_class = GameSerializer

    def post(self, request):
        try:
            player_id = request.data.get("player_id")
            game_title = request.data.get("title")
            game_values = request.data.get("values")

            tasks_to_create = []
            with transaction.atomic():
                created_game = Game.create_with_unique_code(game_title)
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
                .order_by("tasks__grid_column")
                .first()
            )
            serializer = self.serializer_class(game)
            response = Response(
                {"status": "success", "game": serializer.data}, status=200
            )
        except Exception as e:
            logger.exception("Unexpected Error: ", exc_info=e)
            sentry_sdk.capture_exception(e)
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
        try:
            game_code = request.data.get("code")
            player_id = request.data.get("player_id")
            game = (
                Game.objects.filter(code=game_code)
                .prefetch_related("tasks", "players")
                .order_by("tasks__grid_column")
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
            sentry_sdk.capture_exception(e)
            response = Response(
                {"status": "error", "message": "Unexpected Error"}, status=500
            )

        return response
