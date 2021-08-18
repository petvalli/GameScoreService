import json
from jsonschema import validate, ValidationError
from flask import Response, request, url_for
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from gamescoreservice.models import Score, Player, Level, Game
from gamescoreservice import db
from gamescoreservice.utils import ScoreBuilder, create_error_response
from gamescoreservice.constants import *


class ScoreItem(Resource):

    def get(self, game, level, player):
        # Work-around for score item query. Fix it with better time.
        level_query = Level.query.join(Game).filter(Game.name == game, Level.name == level).first()
        db_entry = Score.query.join(Level).join(Player).filter(
                Level.id == level_query.id,
                Player.unique_name == player
            ).first()
        if db_entry is None:
            return create_error_response(404, "Not found", "Score wasn't found.")

        body = ScoreBuilder(
            name=player,
            value=db_entry.value,
            type=db_entry.level.type,
            date=db_entry.date
        )
        body.add_namespace("gss", LINK_RELATIONS_URL)
        body.add_control("self", url_for("api.scoreitem", player=player, game=game, level=level))
        body.add_control("profile", SCORE_PROFILE)
        body.add_control("up", url_for("api.levelitem", game=game, level=level))
        body.add_control("author", url_for("api.playeritem", player=player))
        body.add_control_scores_by(player)
        body.add_control_edit_score(game, level, player)
        body.add_control_delete(url_for("api.scoreitem", player=player, game=game, level=level))

        return Response(json.dumps(body), 200, mimetype=MASON)

    def put(self, game, level, player):
        if not request.json:
            return create_error_response(415, "Unsupported media type", "Requests must be JSON")
        try:
            validate(request.json, Score.get_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))

        # Work-around for score item query. Fix it with better time.
        level_query = Level.query.join(Game).filter(Game.name == game, Level.name == level).first()
        db_entry = Score.query.join(Level).join(Player).filter(
                Level.id == level_query.id,
                Player.unique_name == player
            ).first()
        if db_entry is None:
            return create_error_response(404, "Not found", "Score wasn't found.")

        # Check if the player exists in the database and the password is correct
        ply = request.json["player"]
        pw = request.json["password"]
        db_player = Player.query.filter_by(unique_name=ply).first()
        if db_player is None:
            return create_error_response(404, "Not found", "Player wasn't found.")
        elif ply != player:
            return create_error_response(403, "Forbidden", "Score owner cannot be changed.")
        elif db_player.password.lower() != pw.lower():
            return create_error_response(401, "Unauthorized", "Invalid password.")

        # Set new data
        db_entry.value = request.json["value"]
        db_entry.date = datetime.now().isoformat(' ', 'seconds')
        if "date" in request.json:
            if request.json["date"] != "":
                db_entry.date = request.json["date"]
                # Add timezone handling

        db.session.commit()

        return Response(status=204)

    def delete(self, game, level, player):
        # Work-around for score item query. Fix it with better time.
        level_query = Level.query.join(Game).filter(Game.name == game, Level.name == level).first()
        db_entry = Score.query.join(Level).join(Player).filter(
                Level.id == level_query.id,
                Player.unique_name == player
            ).first()
        if db_entry is None:
            return create_error_response(404, "Not found", "Score wasn't found.")

        db.session.delete(db_entry)
        db.session.commit()

        return Response(status=204)
