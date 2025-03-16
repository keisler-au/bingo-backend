from django.test import TestCase
from unittest.mock import patch, AsyncMock
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from game.consumers import TaskUpdatesConsumer
from channels.routing import URLRouter
from django.urls import path

class TaskUpdatesConsumerTest(TestCase):
    @patch('os.getenv')
    @patch('redis.StrictRedis')
    async def test_connect(self, MockStrictRedis, mock_getenv):
        # Mock environment variables
        mock_getenv.return_value = 'localhost'
        
        # Mock Redis connection
        mock_redis_instance = AsyncMock()
        MockStrictRedis.return_value = mock_redis_instance

        # Create a mock group name
        game_id = '123'
        player_id = '456'
        group_name = f"game_{game_id}"
        application = URLRouter([
            path("game_updates/<str:game_id>/<str:player_id>/", TaskUpdatesConsumer.as_asgi()),
        ])
        # Setup WebSocket communicator for testing the consumer
        communicator = WebsocketCommunicator(application, f"/game_updates/{game_id}/{player_id}/")
        
        # Connect to the WebSocket
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Check if the group_add method was called on the channel layer
        channel_layer = get_channel_layer()
        group_add_mock = AsyncMock()
        channel_layer.group_add = group_add_mock
        
        # Trigger the consumer connect method
        await TaskUpdatesConsumer.connect(self)

        # Check if the consumer joins the group
        group_add_mock.assert_called_once_with(group_name, communicator.channel_name)

        # Check if the Redis client was initialized correctly
        MockStrictRedis.assert_called_once_with(
            host='localhost', port='localhost', password=None, ssl=True, decode_responses=True
        )
        
        # Check if the send_queued_messages method was called
        send_queued_messages_mock = AsyncMock()
        consumer_instance = TaskUpdatesConsumer()
        consumer_instance.send_queued_messages = send_queued_messages_mock
        await consumer_instance.connect()

        send_queued_messages_mock.assert_called_once()

        # Close the WebSocket connection
        await communicator.disconnect()

    # @patch("redis.StrictRedis")
    # def test_disconnect(self, MockRedis):
    #     # Mock Redis instance
    #     mock_redis = MagicMock()
    #     MockRedis.return_value = mock_redis

    #     # Set up the WebSocket communicator and mock the group name and player ID
    #     communicator = WebsocketCommunicator(TaskUpdatesConsumer.as_asgi(), "ws://testserver/")
    #     communicator.channel_name = "test_channel"
    #     communicator.group_name = "test_group"
    #     communicator.player_id = "player_123"

    #     # Mock channel layer to test group discard
    #     mock_channel_layer = MagicMock()
    #     get_channel_layer = MagicMock(return_value=mock_channel_layer)

    #     # Ensure the consumer connects first
    #     self.assertTrue(communicator.connect())

    #     # Call the disconnect method
    #     async def disconnect_task():
    #         await communicator.disconnect(1000)

    #     disconnect_task()

    #     # Assertions
    #     mock_redis.rpush.assert_called_once_with("test_group_queue", "player_123")
    #     mock_redis.expire.assert_called_once_with("test_group_queue", 86400)
    #     mock_channel_layer.group_discard.assert_called_once_with("test_group", "test_channel")


    # @patch('redis.StrictRedis')
    # @patch('myapp.consumers.TaskUpdatesConsumer.enqueue_message')  # Mock the enqueue_message method to isolate the test
    # async def test_receive_heartbeat(self, mock_enqueue, MockRedis):
    #     # Set up mock redis
    #     mock_redis = MockRedis.return_value
    #     mock_redis.get.return_value = None

    #     # Create a WebSocket communicator
    #     communicator = WebsocketCommunicator(application, "ws/task_updates/")
    #     connected, subprotocol = await communicator.connect()

    #     # Test heartbeat message
    #     await communicator.send_json_to({"message": "heartbeat"})
    #     response = await communicator.receive_json_from()
        
    #     # Assert the response is the expected heartbeat response
    #     self.assertEqual(response, {"message": "thump"})

    #     # Close connection
    #     await communicator.disconnect()

    # @patch('redis.StrictRedis')
    # @patch('myapp.consumers.TaskUpdatesConsumer.enqueue_message')  # Mock the enqueue_message method to isolate the test
    # async def test_receive_task_update(self, mock_enqueue, MockRedis):
    #     # Set up mock redis
    #     mock_redis = MockRedis.return_value
    #     mock_redis.get.return_value = None

    #     # Create a mock task update message
    #     task_update = {
    #         "id": 123,
    #         "completed_by": {"id": 456},
    #         "last_updated": "2025-03-16T12:00:00Z"
    #     }

    #     # Create a WebSocket communicator
    #     communicator = WebsocketCommunicator(application, "ws/task_updates/")
    #     connected, subprotocol = await communicator.connect()

    #     # Send task update message
    #     await communicator.send_json_to(task_update)

    #     # Mocking the update_task method of the consumer to return a task
    #     with patch.object(TaskUpdatesConsumer, 'update_task', return_value={"task": "task_updated"}):
    #         await communicator.receive_json_from()

    #         # Mock the group_send call to verify it was sent
    #         mock_group_send = patch.object(get_channel_layer(), 'group_send').start()

    #         # Check that group_send was called with the correct task data
    #         await communicator.receive_json_from()
    #         mock_group_send.assert_called_with(
    #             "ws_task_updates", {"type": "task_update", "task": {"task": "task_updated"}}
    #         )

    #     # Close connection
    #     await communicator.disconnect()