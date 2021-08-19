import json
from jsonschema import validate, ValidationError
from flask import Response, request, url_for
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from gamescoreservice.models import Player
from gamescoreservice import db
from gamescoreservice.utils import ScoreBuilder, create_error_response
from gamescoreservice.constants import *


class PlayerCollection(Resource):
    """
    The PlayerCollection resource supports GET and POST methods.
    Possible response codes:
    200 with a successful GET
    201 with a successful POST
    400 if JSON validating fails
    409 if item exists already
    415 if request is not JSON
    """

    def get(self):
        body = ScoreBuilder()
        body.add_namespace("gss", LINK_RELATIONS_URL)
        body.add_control("self", url_for("api.playercollection"))
        body.add_control_games_all()
        body.add_control_add_player()
        body["items"] = []
        for db_entry in Player.query.all():
            item = ScoreBuilder(
                name=db_entry.name,
                unique_name=db_entry.unique_name
            )
            item.add_control("self", url_for("api.playeritem", player=db_entry.unique_name))
            item.add_control("profile", PLAYER_PROFILE)
            body["items"].append(item)
        return Response(json.dumps(body), 200, mimetype=MASON)

    def post(self):
        if not request.json:
            return create_error_response(415, "Unsupported media type", "Requests must be JSON")

        try:
            validate(request.json, Player.get_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))

        player = Player()
        player.name = request.json["name"]
        player.password = request.json["password"]
        if "unique_name" in request.json:
            player.unique_name = request.json["unique_name"]
        else:
            player.unique_name = request.json["name"].lower().replace(" ", "_")

        try:
            db.session.add(player)
            db.session.commit()
        except IntegrityError:
            return create_error_response(409, "Already exists",
                                         "Player '{}' already exists.".format(player.unique_name)
                                         )

        return Response(status=201, headers={
            "Location": url_for("api.playeritem", player=player.unique_name)
        })


class PlayerItem(Resource):
    """
    The PlayerItem resource supports GET, PUT, and DELETE methods.
    Possible response codes:
    200 with a successful GET
    204 with a successful PUT or DELETE
    301 if item's location changes
    400 if JSON validating fails
    401 if invalid password
    404 if item was not found
    409 if item exists already
    415 if request is not JSON
    """

    def get(self, player):
        db_entry = Player.query.filter_by(unique_name=player).first()
        if db_entry is None:
            return create_error_response(404, "Not found", "Player '{}' wasn't found.".format(player))

        body = ScoreBuilder(
            name=db_entry.name,
            unique_name=db_entry.unique_name
        )
        body.add_namespace("gss", LINK_RELATIONS_URL)
        body.add_control("self", url_for("api.playeritem", player=player))
        body.add_control("profile", PLAYER_PROFILE)
        body.add_control("collection", url_for("api.playercollection"))
        body.add_control_scores_by(player)
        body.add_control_delete(url_for("api.playeritem", player=player))
        body.add_control_edit_player(player)

        return Response(json.dumps(body), 200, mimetype=MASON)

    def put(self, player):
        status = 204
        if not request.json:
            return create_error_response(415, "Unsupported media type", "Requests must be JSON")
        try:
            validate(request.json, Player.get_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))

        db_entry = Player.query.filter_by(unique_name=player).first()
        if db_entry is None:
            return create_error_response(404, "Not found", "Player '{}' wasn't found.".format(player))

        uname = request.json["unique_name"]
        if db_entry.unique_name != uname and Player.query.filter_by(unique_name=uname).first():
            return create_error_response(409, "Already exists", "Player '{}' already exists.".format(uname))

        if db_entry.password.lower() != request.json["password"].lower():
            return create_error_response(401, "Unauthorized", "Invalid password.")

        if db_entry.unique_name != uname:
            status = 301
            headers = {"Location": url_for("api.playeritem", player=uname)}
        else:
            headers = None

        db_entry.name = request.json["name"]
        db_entry.unique_name = request.json["unique_name"]
        db_entry.password = request.json["password"]
 
        db.session.commit()

        return Response(status=status, headers=headers)

    def delete(self, player):
        db_entry = Player.query.filter_by(unique_name=player).first()
        if db_entry is None:
            return create_error_response(404, "Not found", "Player wasn't found.")

        db.session.delete(db_entry)
        db.session.commit()

        return Response(status=204)


class ScoresByCollection(Resource):
    """
    The ScoresByCollection resource supports the GET method.
    Possible response codes:
    200 with a successful GET
    404 if collection was not found
    """

    def get(self, player):
        db_entry = Player.query.filter_by(unique_name=player).first()
        if db_entry is None:
            return create_error_response(404, "Not found", "Player '{}' wasn't found.".format(player))

        body = ScoreBuilder()
        body.add_namespace("gss", LINK_RELATIONS_URL)
        body.add_control("self", url_for("api.scoresbycollection", player=player))
        body.add_control("author", url_for("api.playeritem", player=player))
        body["items"] = []
        for db_item in db_entry.scores:
            item = ScoreBuilder(
                game=db_item.level.game.name,
                level=db_item.level.name,
                value=db_item.value,
                type=db_item.level.type,
                date=db_item.date
            )
            item.add_control("self", url_for("api.scoreitem",
                                             player=db_entry.unique_name,
                                             game=db_item.level.game.name,
                                             level=db_item.level.name
                                             )
                             )
            item.add_control("profile", SCORE_PROFILE)
            body["items"].append(item)
        return Response(json.dumps(body), 200, mimetype=MASON)
