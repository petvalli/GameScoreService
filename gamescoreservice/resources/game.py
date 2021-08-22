import json
from jsonschema import validate, ValidationError
from flask import Response, request, url_for
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from gamescoreservice.models import Game, Level
from gamescoreservice import db
from gamescoreservice.utils import ScoreBuilder, create_error_response
from gamescoreservice.constants import *


class GameCollection(Resource):
    """
    The GameCollection resource supports GET and POST methods.
    Possible response codes:
    200 with a successful GET
    201 with a successful POST
    400 if JSON validating fails
    409 if item exists already
    415 if request is not JSON
    """

    def get(self):
        """
        GET method for the Game collection. Lists Game items.
        """

        body = ScoreBuilder()
        body.add_namespace("gss", LINK_RELATIONS_URL)
        body.add_control("self", url_for("api.gamecollection"))
        body.add_control_players_all()
        body.add_control_add_game()
        body["items"] = []
        for db_entry in Game.query.all():
            item = ScoreBuilder(
                name=db_entry.name,
                publisher=db_entry.publisher,
                genre=db_entry.genre
            )
            item.add_control("self", url_for("api.gameitem", game=db_entry.name))
            item.add_control("profile", GAME_PROFILE)
            body["items"].append(item)
        return Response(json.dumps(body), 200, mimetype=MASON)

    def post(self):
        """
        POST method for the Game collection. Adds a new Game and includes the Location header in
        the response.
        """

        if not request.json:
            return create_error_response(415, "Unsupported media type", "Requests must be JSON")
        try:
            validate(request.json, Game.get_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))

        game = Game()
        game.name = request.json["name"]

        # Treat missing request elements as empty strings
        if "publisher" in request.json:
            game.publisher = request.json["publisher"]
        else:
            game.publisher = ""
        if "genre" in request.json:
            game.genre = request.json["genre"]
        else:
            game.genre = ""

        try:
            db.session.add(game)
            db.session.commit()
        except IntegrityError:
            return create_error_response(409, "Already exists",
                                         "Game '{}' already exists.".format(game.name)
                                         )

        return Response(status=201, headers={
            "Location": url_for("api.gameitem", game=game.name)
        })


class GameItem(Resource):
    """
    The GameItem resource supports GET, PUT, POST, and DELETE methods.
    Possible response codes:
    200 with a successful GET
    201 with a successful POST
    204 with a successful PUT or DELETE
    301 if item's location changes
    400 if JSON validating fails
    404 if item was not found
    409 if item exists already
    415 if request is not JSON
    """

    def get(self, game):
        """
        GET method for the Game item information. Lists Level items.

        :param game: Game's name
        """

        db_entry = Game.query.filter_by(name=game).first()
        if db_entry is None:
            return create_error_response(404, "Not found", "Game '{}' wasn't found.".format(game))

        body = ScoreBuilder(
            name=db_entry.name,
            publisher=db_entry.publisher,
            genre=db_entry.genre
        )
        body.add_namespace("gss", LINK_RELATIONS_URL)
        body.add_control("self", url_for("api.gameitem", game=game))
        body.add_control("profile", GAME_PROFILE)
        body.add_control("collection", url_for("api.gamecollection"))
        body.add_control_add_level(game)
        body.add_control_edit_game(game)
        body.add_control_delete(url_for("api.gameitem", game=game))
        body["items"] = []
        for db_item in db_entry.levels:
            item = ScoreBuilder(
                name=db_item.name
            )
            item.add_control("self", url_for("api.levelitem", game=game, level=db_item.name))
            item.add_control("profile", LEVEL_PROFILE)
            body["items"].append(item)

        return Response(json.dumps(body), 200, mimetype=MASON)

    def put(self, game):
        """
        PUT method for editing the Game item. Includes the Location header if the name is changed.

        :param game: Game's name
        """

        status = 204
        if not request.json:
            return create_error_response(415, "Unsupported media type", "Requests must be JSON")
        try:
            validate(request.json, Game.get_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))

        db_entry = Game.query.filter_by(name=game).first()
        if db_entry is None:
            return create_error_response(404, "Not found", "Game '{}' wasn't found.".format(game))

        name = request.json["name"]
        if db_entry.name != name and Game.query.filter_by(name=name).first():
            return create_error_response(409, "Already exists", "Game '{}' already exists.".format(name))

        # When changing game's name, location changes too
        if db_entry.name != name:
            status = 301
            headers = {"Location": url_for("api.gameitem", game=name)}
        else:
            headers = None

        # Treat missing request elements as empty strings
        db_entry.name = name
        if "publisher" in request.json:
            db_entry.publisher = request.json["publisher"]
        else:
            db_entry.publisher = ""
        if "genre" in request.json:
            db_entry.genre = request.json["genre"]
        else:
            db_entry.genre = ""

        db.session.commit()

        return Response(status=status, headers=headers)

    def post(self, game):
        """
        POST method for the Game item. Adds a new level and includes the Location header in the
        response.

        :param game: Game's name
        """

        if not request.json:
            return create_error_response(415, "Unsupported media type", "Requests must be JSON")
        try:
            validate(request.json, Level.get_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))

        db_entry = Game.query.filter_by(name=game).first()
        if db_entry is None:
            return create_error_response(404, "Not found", "Game '{}' wasn't found.".format(game))

        level = Level()
        level.name = request.json["name"]
        level.type = request.json["type"]
        level.order = request.json["order"]
        db_entry.levels.append(level)

        try:
            db.session.commit()
        except IntegrityError:
            return create_error_response(409, "Already exists",
                                         "Level '{}' already exists.".format(level.name)
                                         )

        return Response(status=201, headers={
            "Location": url_for("api.levelitem", game=game, level=level.name)
        })

    def delete(self, game):
        """
        DELETE method for the Game item. Deletes the resource.

        :param game: Game's name
        """

        db_entry = Game.query.filter_by(name=game).first()
        if db_entry is None:
            return create_error_response(404, "Not found", "Game '{}' wasn't found.".format(game))

        db.session.delete(db_entry)
        db.session.commit()

        return Response(status=204)
