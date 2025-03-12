from django.urls import re_path

from game.consumers import TaskUpdatesConsumer

websocket_urlpatterns = [
    re_path(r"ws/socket-server/(?P<game_id>\d+)/$", TaskUpdatesConsumer.as_asgi()),
]
