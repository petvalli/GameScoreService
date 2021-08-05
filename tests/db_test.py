"""
Test structure is based on an example and instructions from the Programmable Web Project course.
"""

import os
import pytest
import tempfile
import time
from datetime import datetime
from sqlalchemy.engine import Engine
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError, StatementError

from gamescoreservice import create_app, db
from gamescoreservice.models import Game, Level, Score, Player


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest.fixture
def app():
    db_fd, db_fname = tempfile.mkstemp()
    config = {
        "SQLALCHEMY_DATABASE_URI": "sqlite:///" + db_fname,
        "TESTING": True
    }
    
    app = create_app(config)
    
    with app.app_context():
        db.create_all()
        
    yield app
    
    os.close(db_fd)
    os.unlink(db_fname)


def _get_player(n="Driver 1", u="driver_1", p="8e72e8b36289c5777861de5d869bf9aa"):
    return Player(
        name=n,
        unique_name=u,
        password=p
    )


def _get_game(n="Stunt Car Racer", p="MicroStyle", g="Racing"):
    return Game(
        name=n,
        publisher=p,
        genre=g
    )


def _get_level(n="Stepping Stones", t="time", o="ascending"):
    return Level(
        name=n,
        type=t,
        order=o
    )


def _get_score(v=53690, d="2021-08-05 19:55:08"):
    return Score(
        value=v,
        date=d
    )


def test_create_instances(app):
    """
    Try to create one instance of each model with valid values and test that they were added to
    the database correctly.
    """

    with app.app_context():
        # Get example values
        player = _get_player()
        game = _get_game()
        level = _get_level()
        score = _get_score()

        # Add relationships
        level.game = game
        score.level = level
        score.player = player

        # Add everything into the database
        db.session.add(player)
        db.session.add(game)
        db.session.add(level)
        db.session.add(score)

        db.session.commit()

        # Check for correct amount of created instances
        assert Player.query.count() == 1
        assert Game.query.count() == 1
        assert Level.query.count() == 1
        assert Score.query.count() == 1

        # Retrieve instances
        db_player = Player.query.first()
        db_game = Game.query.first()
        db_level = Level.query.first()
        db_score = Score.query.first()

        # Check relationships
        assert db_level.game == db_game
        assert db_score.level == db_level
        assert db_score.player == db_player
        assert db_level in db_game.levels
        assert db_score in db_level.scores
        assert db_score in db_player.scores
