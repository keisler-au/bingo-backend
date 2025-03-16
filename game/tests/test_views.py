from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from game.models import Game, Player, Task
from unittest.mock import patch


class CreatePlayerTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/create_player/"

    def test_create_player_success(self):
        # Simulating a successful player creation
        data = {"data": "Player1"}  # Data to create the player
        response = self.client.post(self.url, data, format="json")
        
        # Check if the player was created successfully
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(response.data["player"]["name"], "Player1")
        
        # Check if the player exists in the database
        player = Player.objects.get(name="Player1")
        self.assertIsNotNone(player)

    def test_create_player_missing_name(self):
        # Simulating a request with missing player name
        data = {"data": ""}  # Missing player name
        response = self.client.post(self.url, data, format="json")

        # Check for error due to missing name
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)  # Adjust depending on how you handle this error
        self.assertEqual(response.data["status"], "error")
        self.assertIn("message", response.data)

    def test_create_player_unexpected_error(self):
        # Simulate an unexpected error (e.g., database issue)
        data = {"data": "Player2"}
        
        # Patch the code to force an exception in the view
        with self.assertRaises(Exception):
            self.client.post(self.url, data, format="json")

        # Alternatively, you can simulate an exception in the view method and check for logging.
        # This requires using mock objects to simulate the error and check the logs.
        # You can mock sentry_sdk.capture_exception and logger.exception if needed.


class CreateAndRetrieveGameTest(TestCase):
    def setUp(self):
        # Setup a mock player to test the view
        self.player = Player.objects.create(id=1, name="Test Player")

        # Setup test data for the game creation
        self.game_data = {
            "data": {
                "player_id": self.player.id,
                "title": "Test Game",
                "values": [["X", "O", "X"], ["O", "X", "O"], ["X", "X", "X"]]
            }
        }
        self.url = "/publish_game/"  # Replace with the actual URL endpoint of the view

    @patch("game.views.Player.objects.get")
    @patch("game.views.Game.create_with_unique_code")
    @patch("game.views.Task.objects.bulk_create")
    def test_create_and_retrieve_game_success(self, mock_bulk_create, mock_create_game, mock_get_player):
        # Mocking the player retrieval and game creation
        mock_get_player.return_value = self.player
        mock_create_game.return_value = MagicMock(id=1, title="Test Game")
        mock_bulk_create.return_value = None

        # Create an API client to send the request
        client = APIClient()
        response = client.post(self.url, self.game_data, format="json")

        # Assert status code is 200
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("status", response.data)
        self.assertEqual(response.data["status"], "success")
        self.assertIn("game", response.data)

    @patch("game.views.Player.objects.get")
    @patch("game.views.Game.create_with_unique_code")
    @patch("game.views.Task.objects.bulk_create")
    def test_create_and_retrieve_game_error(self, mock_bulk_create, mock_create_game, mock_get_player):
        # Simulate an error during the player retrieval
        mock_get_player.side_effect = Exception("Player not found")

        # Create an API client to send the request
        client = APIClient()
        response = client.post(self.url, self.game_data, format="json")

        # Assert status code is 500 (Internal Server Error)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("status", response.data)
        self.assertEqual(response.data["status"], "error")
        self.assertIn("message", response.data)
        self.assertEqual(response.data["message"], "Unexpected Error")


class RetrieveGameTestCase(TestCase):
    def setUp(self):
        # Setup initial test data (mock data for Game and Player)
        self.client = APIClient()
        self.game = Game.objects.create(code="TEST123")  # Create a game object
        self.player = Player.objects.create(id=1)  # Create a player object
        self.url = "/join_game/"  # Replace with your actual URL

    @patch("game.views.Game.objects.filter")
    @patch("game.views.Player.objects.get")
    @patch("game.views.GameSerializer")
    def test_post_game_found(self, mock_serializer, mock_get_player, mock_filter_game):
        # Prepare mock return values
        mock_filter_game.return_value.prefetch_related.return_value.first.return_value = self.game
        mock_get_player.return_value = self.player
        
        mock_serializer.return_value.data = {
            "code": self.game.code,
            "tasks": [],  # Add your tasks here if needed
            "players": [self.player.id],
        }
        
        # Create your request payload
        payload = {
            "data": {
                "code": "TEST123",
                "player_id": 1
            }
        }

        # Make POST request to the endpoint
        response = self.client.post(self.url, payload, format="json")

        # Check the response status and content
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        self.assertIn("game", response.data)
        self.assertEqual(response.data["game"]["code"], self.game.code)
        mock_filter_game.assert_called_once_with(code="TEST123")
        mock_get_player.assert_called_once_with(id=1)

    @patch("game.views.Game.objects.filter")
    @patch("game.views.Player.objects.get")
    def test_post_game_not_found(self, mock_get_player, mock_filter_game):
        # Mock game not found
        mock_filter_game.return_value.prefetch_related.return_value.first.return_value = None
        mock_get_player.return_value = self.player
        
        payload = {
            "data": {
                "code": "INVALID_CODE",
                "player_id": 1
            }
        }

        response = self.client.post(self.url, payload, format="json")

        # Check the response status and content for error
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["status"], "error")
        self.assertEqual(response.data["message"], "Game not found or game has no players")

    @patch("game.views.Game.objects.filter")
    @patch("game.views.Player.objects.get")
    def test_post_unexpected_error(self, mock_get_player, mock_filter_game):
        # Mock an unexpected exception during game retrieval
        mock_filter_game.side_effect = Exception("Unexpected error")
        
        payload = {
            "data": {
                "code": "TEST123",
                "player_id": 1
            }
        }

        response = self.client.post(self.url, payload, format="json")

        # Check the response status and content for error
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data["status"], "error")
        self.assertEqual(response.data["message"], "Unexpected Error")
