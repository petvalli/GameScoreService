from flask import Blueprint
from flask_restful import Api

api_bp = Blueprint("api", __name__, url_prefix="/api")
api = Api(api_bp)

import json
from gamescoreservice.resources.player import PlayerCollection, PlayerItem, ScoresByCollection
from gamescoreservice.resources.score import ScoreItem
from gamescoreservice.resources.game import GameCollection, GameItem
from gamescoreservice.resources.level import LevelItem
from gamescoreservice.constants import *
from gamescoreservice.utils import ScoreBuilder
from flask import Response, redirect


# Resources:

api.add_resource(PlayerCollection, "/players/")
api.add_resource(PlayerItem, "/players/<player>/")
api.add_resource(ScoresByCollection, "/players/<player>/scores/")
api.add_resource(GameCollection, "/games/")
api.add_resource(GameItem, "/games/<game>/")
api.add_resource(LevelItem, "/games/<game>/<level>/")
api.add_resource(ScoreItem, "/games/<game>/<level>/<player>/")


# View functions:

@api_bp.route("/")
def entry_point():
    """
    Entry point has controls to go to list of all games or all players.
    """

    body = ScoreBuilder()
    body.add_namespace("gss", LINK_RELATIONS_URL)
    body.add_control_games_all()
    body.add_control_players_all()
    return Response(json.dumps(body), 200, mimetype=MASON)


@api_bp.route(LINK_RELATIONS_URL)
def redirect_link_relations():
    """
    Redirect link relations to the Apiary documentation.
    """

    return redirect(APIARY_URL + "link-relations")


@api_bp.route("/profiles/<profile>/")
def redirect_profiles(profile):
    """
    Redirect profiles to the Apiary documentation.
    """

    return redirect(APIARY_URL + "profiles")
