from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from game.models import Game, Player
from game.serializers import GameSerializer


class CreatePlayerTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/game/create_player/"

    def test_create_player_success(self):
        data = {"data": "Player1"}
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(response.data["player"]["name"], "Player1")

        player = Player.objects.get(name="Player1")
        self.assertIsNotNone(player)

    def test_create_player_error(self):
        data = ""
        with self.assertRaises(Exception):
            self.client.post(self.url, data)


class CreateAndRetrieveGameTest(TestCase):
    def setUp(self):
        self.player = Player.objects.create(id=1, name="Test Player")
        self.game_data = {
            "data": {
                "player_id": self.player.id,
                "title": "Test Game",
                "values": [["X", "O", "X"], ["O", "X", "O"], ["X", "X", "X"]],
            }
        }
        self.url = "/game/publish_game/"

    def test_create_and_retrieve_game(self):
        """Game created in db and serialized data sent back to client"""
        with self.assertNumQueries(1):
            games = (
                Game.objects.prefetch_related("players", "tasks")
                .order_by("tasks__grid_column")
                .all()
            )
            GameSerializer(games, many=True).data
        pass

    def test_failed_create_game(self):
        """Game not created in db and 500 status sent back to client"""
        pass

    def test_retry_create_unique_game_code(self):
        """Game code unique constraint violated and get_random_string called again"""
        pass

    def test_failed_create_and_retrieve_game(self):
        """Game created in db but serialization failed and 500 sent to client"""
        pass


class RetrieveGameTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.game = Game.objects.create(code="123456")
        self.player = Player.objects.create(id=1)
        self.url = "/game/join_game/"

    def test_game_retrieved(self):
        """Game successfully pulled from db and sent back to client"""
        pass

    def test_game_not_found(self):
        """Game not found in db and 404 sent back to client"""
        pass

    def test_game_retrieval_error(self):
        """Game retrieval resulted in a error and 500 sent back to client"""
        pass
