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


def test_create_and_retrieve_instances(app):
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

        # Add all into the database
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

        # Retrieve instances (by different filtering options)
        db_game = Game.query.first()
        db_level = Level.query.first()
        db_score = Score.query.filter(Score.value > 20000).first()
        db_player = Player.query.filter_by(unique_name="driver_1").first()

        # Check relationships
        assert db_level.game == db_game
        assert db_score.level == db_level
        assert db_score.player == db_player
        assert db_level in db_game.levels
        assert db_score in db_level.scores
        assert db_score in db_player.scores


def test_update_instances(app):
    """
    Try to update all instances.
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

        # Add all into the database
        db.session.add(player)
        db.session.add(game)
        db.session.add(level)
        db.session.add(score)
        db.session.commit()

        # Update instances
        player.name = "New player"
        game.publisher = "New publisher"
        level.type = "number"
        score.value = 2021
        db.session.commit()

        # Test updates
        db_player = Player.query.first()
        db_game = Game.query.first()
        db_level = Level.query.first()
        db_score = Score.query.first()
        assert db_player.name == "New player"
        assert db_game.publisher == "New publisher"
        assert db_level.type == "number"
        assert db_score.value == 2021


def test_delete_player(app):
    """
    Try to delete the player instance and check if ondelete works as expected.
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

        # Add all into the database
        db.session.add(player)
        db.session.add(game)
        db.session.add(level)
        db.session.add(score)
        db.session.commit()

        # Delete player
        db.session.delete(player)
        db.session.commit()

        # Check if player and score (ondelete) were deleted, but rest are untouched
        assert Player.query.count() == 0
        assert Score.query.count() == 0
        assert Game.query.count() == 1
        assert Level.query.count() == 1


def test_delete_score(app):
    """
    Try to delete the score instance and check if ondelete works as expected.
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

        # Add all into the database
        db.session.add(player)
        db.session.add(game)
        db.session.add(level)
        db.session.add(score)
        db.session.commit()

        # Delete score
        db.session.delete(score)
        db.session.commit()

        # Check if score was deleted, but rest are untouched
        assert Player.query.count() == 1
        assert player.scores == []
        assert Score.query.count() == 0
        assert Game.query.count() == 1
        assert Level.query.count() == 1


def test_delete_level(app):
    """
    Try to delete the level instance and check if ondelete works as expected.
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

        # Add all into the database
        db.session.add(player)
        db.session.add(game)
        db.session.add(level)
        db.session.add(score)
        db.session.commit()

        # Delete level
        db.session.delete(level)
        db.session.commit()

        # Check if level and score (ondelete) were deleted, but rest are untouched
        assert Player.query.count() == 1
        assert Game.query.count() == 1
        assert Level.query.count() == 0
        assert Score.query.count() == 0


def test_delete_game(app):
    """
    Try to delete the game instance and check if ondelete works as expected.
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

        # Add all into the database
        db.session.add(player)
        db.session.add(game)
        db.session.add(level)
        db.session.add(score)
        db.session.commit()

        # Delete game
        db.session.delete(game)
        db.session.commit()

        # Check if game, level (ondelete), and score (ondelete) were deleted, but player exists.
        assert Player.query.count() == 1
        assert Game.query.count() == 0
        assert Level.query.count() == 0
        assert Score.query.count() == 0


def test_error_situations(app):
    """
    Try possible error situations.
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

        # Add all into the database
        db.session.add(player)
        db.session.add(game)
        db.session.add(level)
        db.session.add(score)
        db.session.commit()

        # Test uniqueness with a player (unique_name (u) shouldn't be the same)
        player_2 = _get_player(n="Test player", u=None, p="cdf6472b7d43a9948fde81be66a0d769")
        db.session.add(player_2)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # Test uniqueness with a game (game name (n) shouldn't be the same)
        game_2 = _get_game(n=None, p="publisher 2", g="genre 2")
        db.session.add(game_2)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # Test uniqueness with a level item for a game (no levels with the same name allowed)
        level_2 = _get_level()
        level_2.game = game
        db.session.add(level_2)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # Test uniqueness with a score item for a level by a player (only one is allowed)
        score_2 = _get_score(v=1234, d=datetime.now().isoformat(' ', 'seconds'))
        score_2.level = level
        score_2.player = player
        db.session.add(score_2)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # Try to set invalid foreign keys
        score.player_id = 9999
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        score.level_id = 9999
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        level.game_id = 9999
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()
