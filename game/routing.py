from django.urls import re_path, path
from game.consumers import TaskUpdatesConsumer

websocket_urlpatterns = [
    # re_path(
    #     r"game_updates/(?P<game_id>\d+)/(?P<player_id>\d+)/$",
    #     TaskUpdatesConsumer.as_asgi(),
    # ),
    path(
        "game_updates/<str:game_id>/<str:player_id>/",
        TaskUpdatesConsumer.as_asgi(),
    ),
]
