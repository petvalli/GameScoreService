import json
from jsonschema import validate, ValidationError
from flask import Response, request, url_for
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from gamescoreservice.models import Level, Game, Player, Score
from gamescoreservice import db
from gamescoreservice.utils import ScoreBuilder, create_error_response
from gamescoreservice.constants import *


class LevelItem(Resource):

    def get(self, game, level):
        db_entry = Level.query.join(Game).filter(Game.name == game, Level.name == level).first()
        if db_entry is None:
            return create_error_response(404, "Not found", "Level '{}' wasn't found.".format(level))

        body = ScoreBuilder(
            name=db_entry.name,
            type=db_entry.type,
            order=db_entry.order
        )
        body.add_namespace("gss", LINK_RELATIONS_URL)
        body.add_control("self", url_for("api.levelitem", game=game, level=level))
        body.add_control("profile", LEVEL_PROFILE)
        body.add_control("up", url_for("api.gameitem", game=game))
        body.add_control_add_score(game, level)
        body.add_control_edit_level(game, level)
        body.add_control_delete(url_for("api.levelitem", game=game, level=level))
        body["items"] = []
        for db_item in db_entry.scores:
            item = ScoreBuilder(
                player=db_item.player.name,
                value=db_item.value,
                date=db_item.date
            )
            item.add_control("self", url_for(
                    "api.scoreitem",
                    game=game,
                    level=level,
                    player=db_item.player.unique_name
                )
            )
            item.add_control("profile", SCORE_PROFILE)
            body["items"].append(item)

        return Response(json.dumps(body), 200, mimetype=MASON)

    def put(self, game, level):
        if not request.json:
            return create_error_response(415, "Unsupported media type", "Requests must be JSON")
        try:
            validate(request.json, Level.get_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))

        db_entry = Level.query.join(Game).filter(Game.name == game, Level.name == level).first()
        if db_entry is None:
            return create_error_response(404, "Not found", "Level '{}' wasn't found.".format(level))

        db_entry.name = request.json["name"]
        if "type" in request.json:
            db_entry.type = request.json["type"]
        if "order" in request.json:
            db_entry.order = request.json["order"]

        db.session.commit()

        return Response(status=204)

    def post(self, game, level):
        if not request.json:
            return create_error_response(415, "Unsupported media type", "Requests must be JSON")
        try:
            validate(request.json, Score.get_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))

        db_level = Level.query.join(Game).filter(Game.name == game, Level.name == level).first()
        if db_level is None:
            return create_error_response(404, "Not found", "Level '{}' wasn't found.".format(level))

        # Check if the player exists in the database and the password is correct
        ply = request.json["player"]
        pw = request.json["password"]
        db_player = Player.query.filter_by(unique_name=ply).first()
        if db_player is None:
            return create_error_response(401, "Unauthorized", "Player wasn't found.")
        elif db_player.password.lower() != pw.lower():
            return create_error_response(401, "Unauthorized", "Invalid password.")

        score = Score()
        score.value = request.json["value"]
        if "date" in request.json:
            score.date = request.json["date"]
            # Add timezone handling
        else:
            score.date = datetime.now().isoformat(' ', 'seconds')
        score.level = db_level
        score.player = db_player

        try:
            db.session.add(score)
            db.session.commit()
        except IntegrityError:
            return create_error_response(409, "Already exists", "Score already exists.")

        return Response(status=201, headers={
            "Location": url_for("api.scoreitem", game=game, level=level, player=ply)
        })

    def delete(self, game, level):
        db_entry = Level.query.join(Game).filter(Game.name == game, Level.name == level).first()
        if db_entry is None:
            return create_error_response(404, "Not found", "Level '{}' wasn't found.".format(level))

        db.session.delete(db_entry)
        db.session.commit()

        return Response(status=204)
