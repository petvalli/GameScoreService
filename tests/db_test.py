"""
Test structure based on an example and instructions in the Programmable Web Project course.
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


def _get_game(n="Stunt Car Racer", p="MicroStyle", g="Racing"):
    return Game(
        name=n,
        publisher=p,
        genre=g
    )


def test_create_instances(app):
    with app.app_context():
        game = _get_game()
        db.session.add(game)
        db.session.commit()
        assert Game.query.count() == 1
