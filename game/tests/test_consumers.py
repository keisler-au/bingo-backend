from unittest.mock import AsyncMock, patch

from channels.layers import get_channel_layer
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.test import TestCase, override_settings
from django.urls import path

from game.consumers import TaskUpdatesConsumer

TEST_CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }
}


@override_settings(CHANNEL_LAYERS=TEST_CHANNEL_LAYERS)
class TaskUpdatesConsumerTest(TestCase):
    def setUp(self):
        self.application = URLRouter(
            [
                path("testws/<game_id>/<player_id>", TaskUpdatesConsumer.as_asgi()),
            ]
        )
        self.channel_layer = get_channel_layer()

    @patch(
        "game.consumers.TaskUpdatesConsumer.send_queued_messages",
        new_callable=AsyncMock,
    )
    async def test_connect(self, send_queued_messages_mock):
        """Consumer successfully connects and calls dependencies"""
        communicator = WebsocketCommunicator(self.application, "/testws/1/1")
        self.channel_layer.group_add = AsyncMock()
        connected, subprotocol = await communicator.connect()
        assert connected
        self.channel_layer.group_add.assert_called_once()
        send_queued_messages_mock.assert_called_once()
        await communicator.disconnect()

    async def test_queue_disconnect(self):
        """Updating redis queue succeeds and then consumer successfully disconnects"""
        pass

    async def test_failed_queue_disconnect(self):
        """Updating redis queue fails and then consumer successfully disconnects"""
        pass

    async def test_receive_heartbeat(self):
        """Recieving 'heartbeat' message is successfully responded to with 'thump'"""
        pass

    async def test_receive_task_update(self):
        """Recieving valid task update successfully calls dependencies and sends message to group"""
        pass

    async def test_invalid_recieve_task_update(self):
        """Recieving invalid task update successfully calls dependencies and no message is sent to group"""
        pass

    async def test_update_task(self):
        """Valid task is updated and returned in format"""
        pass

    async def test_invalid_update_task(self):
        """Invalid task is not updated and {} is returned"""
        pass

    async def test_failed_update_task(self):
        """Task update fails and {} is returned"""
        pass

    async def test_send_queued_messages(self):
        """Sending queued messages was succesful"""
        pass

    async def test_failed_send_queued_messages(self):
        """Sending queued messages failed and error was handled"""
        pass
