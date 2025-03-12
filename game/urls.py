from django.urls import path

from game.views import CreateAndRetrieveGame, CreatePlayer, RetrieveGame

urlpatterns = [
    path("publish_game/", CreateAndRetrieveGame.as_view(), name="publish_game"),
    path("join_game/", RetrieveGame.as_view(), name="join_game"),
    path("create_player/", CreatePlayer.as_view(), name="create_player"),
]
