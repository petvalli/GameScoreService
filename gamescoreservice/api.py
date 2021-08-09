from flask import Blueprint
from flask_restful import Api

api_bp = Blueprint("api", __name__, url_prefix="/api")
api = Api(api_bp)

from gamescoreservice.resources.player import PlayerCollection, PlayerItem, ScoresByCollection
from gamescoreservice.resources.score import ScoreItem
from gamescoreservice.resources.game import GameCollection, GameItem
from gamescoreservice.resources.level import LevelItem

api.add_resource(PlayerCollection, "/players/")
api.add_resource(PlayerItem, "/players/<player>/")
api.add_resource(ScoresByCollection, "/players/<player>/scores/")
api.add_resource(GameCollection, "/games/")
api.add_resource(GameItem, "/games/<game>/")
api.add_resource(LevelItem, "/games/<game>/<level>/")
api.add_resource(ScoreItem, "/games/<game>/<level>/<player>/")

#@api.route("/" + API_NAME + "/link-relations/")
#def redirect_to_apiary_link_rels():
#    return redirect(APIARY_URL + "link-relations")
