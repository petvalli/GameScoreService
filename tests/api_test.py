"""
Test structure is based on an example and instructions from the Programmable Web Project course.

Revealed errors:
- Put and delete were missing in Player
- Put didn't check if already exists

"""

import json
import os
import pytest
import tempfile
import time
import hashlib
from datetime import datetime
from jsonschema import validate
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


# based on http://flask.pocoo.org/docs/1.0/testing/
# we don't need a client for database testing, just the db handle
@pytest.fixture
def client():
    db_fd, db_fname = tempfile.mkstemp()
    config = {
        "SQLALCHEMY_DATABASE_URI": "sqlite:///" + db_fname,
        "TESTING": True
    }

    app = create_app(config)

    with app.app_context():
        db.create_all()
        _populate_db()

    yield app.test_client()

    os.close(db_fd)
    os.unlink(db_fname)


def _populate_db():
    from datetime import datetime
    genre = ["Racing", "Puzzle", "Action"]
    p = {}
    for i in range(1, 5):
        p[i] = Player(
            name="Player {}".format(i),
            unique_name="player_{}".format(i),
            password=hashlib.md5("pw {}".format(i).encode("utf-8")).hexdigest()
        )
        db.session.add(p[i])
    for i in range(1, 4):
        g = Game(
            name="Game {}".format(i),
            publisher="Publisher {}".format(i),
            genre=genre[i - 1]
        )
        db.session.add(g)
        db.session.commit()
        for j in range(1, 4):
            lv = Level(
                name="Level {}".format(j),
                game_id=g.id
            )
            db.session.add(lv)
            db.session.commit()
            for k in range(1, 4):
                s = Score(
                    value=k * 100,
                    level=lv,
                    player=p[k],
                    date=datetime.now().isoformat(' ', 'seconds')
                )
                db.session.add(s)
                db.session.commit()


def _get_json_object(model, number=2):
    """
    Creates a valid JSON object for the requested model to be used for PUT and POST tests.
    """

    obj = {}
    if model == "player":
        obj["name"] = "Player {}".format(number)
        obj["unique_name"] = obj["name"].lower().replace(" ", "_")
        obj["password"] = hashlib.md5("pw {}".format(number).encode("utf-8")).hexdigest()
    elif model == "game":
        obj["name"] = "Game {}".format(number)
        obj["publisher"] = "Test publisher"
        obj["genre"] = "Testing"
    elif model == "level":
        obj["name"] = "Level {}".format(number)
        obj["type"] = "time"
        obj["order"] = "ascending"
    elif model == "score":
        obj["value"] = 31337
        obj["date"] = "2021-08-15 21:22:23"
        obj["player"] = "player_{}".format(number)
        obj["password"] = hashlib.md5("pw {}".format(number).encode("utf-8")).hexdigest()

    return obj


# This function is based on the function from the PWP material
def _check_namespace(client, response):
    """
    Checks that the "gss" namespace is found from the response body, and
    that its "name" attribute is a URL that can be accessed.
    """

    ns_href = response["@namespaces"]["gss"]["name"]
    resp = client.get(ns_href)
    # The URL is a redirect (302)
    assert resp.status_code == 302


# This function is taken from the PWP material (with small changes)
def _check_control_get_method(ctrl, client, obj, code=200):
    """
    Checks a GET type control from a JSON object be it root document or an item
    in a collection. Also checks that the URL of the control can be accessed.
    """

    href = obj["@controls"][ctrl]["href"]
    resp = client.get(href)
    assert resp.status_code == code


# This function is taken from the PWP material
def _check_control_delete_method(ctrl, client, obj):
    """
    Checks a DELETE type control from a JSON object be it root document or an
    item in a collection. Checks the control's method in addition to its "href".
    Also checks that using the control results in the correct status code of 204.
    """

    href = obj["@controls"][ctrl]["href"]
    method = obj["@controls"][ctrl]["method"].lower()
    assert method == "delete"
    resp = client.delete(href)
    assert resp.status_code == 204


# This function is taken from the PWP material (with small changes)
def _check_control_put_method(ctrl, client, obj, model, number=2):
    """
    Checks a PUT type control from a JSON object be it root document or an item
    in a collection. In addition to checking the "href" attribute, also checks
    that method, encoding and schema can be found from the control. Also
    validates a valid object against the schema of the control to ensure that
    they match. Finally checks that using the control results in the correct
    status code of 204.
    """

    ctrl_obj = obj["@controls"][ctrl]
    href = ctrl_obj["href"]
    method = ctrl_obj["method"].lower()
    encoding = ctrl_obj["encoding"].lower()
    schema = ctrl_obj["schema"]
    assert method == "put"
    assert encoding == "json"
    body = _get_json_object(model, number)
    if "name" in obj:
        body["name"] = obj["name"]
    validate(body, schema)
    resp = client.put(href, json=body)
    assert resp.status_code == 204


# This function is taken from the PWP material (with small changes)
def _check_control_post_method(ctrl, client, obj, model, number=2):
    """
    Checks a POST type control from a JSON object be it root document or an item
    in a collection. In addition to checking the "href" attribute, also checks
    that method, encoding and schema can be found from the control. Also
    validates a valid object against the schema of the control to ensure that
    they match. Finally checks that using the control results in the correct
    status code of 201.
    """

    ctrl_obj = obj["@controls"][ctrl]
    href = ctrl_obj["href"]
    method = ctrl_obj["method"].lower()
    encoding = ctrl_obj["encoding"].lower()
    schema = ctrl_obj["schema"]
    assert method == "post"
    assert encoding == "json"
    body = _get_json_object(model, number)
    validate(body, schema)
    resp = client.post(href, json=body)
    assert resp.status_code == 201


class TestPlayerCollection(object):
    RESOURCE_URL = "/api/players/"

    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_get_method("gss:games-all", client, body)
        _check_control_post_method("gss:add-player", client, body, "player", 5)
        assert len(body["items"]) == 4
        for item in body["items"]:
            _check_control_get_method("self", client, item)
            # Profiles are redirects (302)
            _check_control_get_method("profile", client, item, 302)

    def test_post(self, client):
        valid = _get_json_object("player", 5)
        
        # test with wrong content type
        resp = client.post(self.RESOURCE_URL, data=json.dumps(valid))
        assert resp.status_code == 415
        
        # test with valid and see that it exists afterward
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201
        assert resp.headers["Location"].endswith(self.RESOURCE_URL + valid["unique_name"] + "/")
        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200
        
        # send same data again for 409
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409
        
        # remove password field for 400
        valid.pop("password")
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400

        # test with valid, but without unique_name
        valid = _get_json_object("player", 6)
        valid.pop("unique_name")
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201


class TestGameCollection(object):
    RESOURCE_URL = "/api/games/"

    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_get_method("gss:players-all", client, body)
        _check_control_post_method("gss:add-game", client, body, "game", 5)
        assert len(body["items"]) == 3
        for item in body["items"]:
            _check_control_get_method("self", client, item)
            # Profiles are redirects (302)
            _check_control_get_method("profile", client, item, 302)

    def test_post(self, client):
        valid = _get_json_object("game", 5)
        
        # test with wrong content type
        resp = client.post(self.RESOURCE_URL, data=json.dumps(valid))
        assert resp.status_code == 415
        
        # test with valid and see that it exists afterward
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201
        assert resp.headers["Location"].endswith(self.RESOURCE_URL + valid["name"].replace(" ", "%20") + "/")
        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200
        
        # send same data again for 409
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409
        
        # remove name field for 400
        valid.pop("name")
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400


class TestScoresByCollection(object):
    RESOURCE_URL = "/api/players/player_2/scores/"
    INVALID_URL = "/api/players/player_inv/scores/"

    def test_get(self, client):
        resp = client.get(self.INVALID_URL)
        assert resp.status_code == 404
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_get_method("author", client, body)
        assert len(body["items"]) == 9
        for item in body["items"]:
            _check_control_get_method("self", client, item)
            # Profiles are redirects (302)
            _check_control_get_method("profile", client, item, 302)


class TestPlayerItem(object):
    
    RESOURCE_URL = "/api/players/player_2/"
    INVALID_URL = "/api/players/player_inv/"
    
    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_get_method("profile", client, body, 302)
        _check_control_get_method("collection", client, body)
        _check_control_get_method("gss:scores-by", client, body)
        _check_control_put_method("edit", client, body, "player")
        _check_control_delete_method("gss:delete", client, body)
        resp = client.get(self.INVALID_URL)
        assert resp.status_code == 404

    def test_put(self, client):
        valid = _get_json_object("player", 2)
        
        # test with wrong content type
        resp = client.put(self.RESOURCE_URL, data=json.dumps(valid))
        assert resp.status_code == 415
        
        resp = client.put(self.INVALID_URL, json=valid)
        assert resp.status_code == 404

        # test with new name
        valid["name"] = "pLayEr 2"
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 204

        # test with wrong password
        valid["password"] = "eaec5029373f916e25da227cc9739c6e"
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 401

        # test with existing player
        valid["unique_name"] = "player_3"
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409

        # remove field for 400
        valid.pop("name")
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400

        # test with new non-existing unique name
        valid = _get_json_object("player", 2)
        valid["unique_name"] = "player_33"
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 301

    def test_delete(self, client):
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 204
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 404
        resp = client.delete(self.INVALID_URL)
        assert resp.status_code == 404


class TestGameItem(object):
    
    RESOURCE_URL = "/api/games/Game 2/"
    INVALID_URL = "/api/games/Invataxi/"
    
    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_get_method("profile", client, body, 302)
        _check_control_get_method("collection", client, body)
        _check_control_post_method("gss:add-level", client, body, "level", 5)
        _check_control_put_method("edit", client, body, "game")
        assert len(body["items"]) == 3
        for item in body["items"]:
            _check_control_get_method("self", client, item)
            _check_control_get_method("profile", client, item, 302)
        _check_control_delete_method("gss:delete", client, body)
        resp = client.get(self.INVALID_URL)
        assert resp.status_code == 404

    def test_put(self, client):
        valid = _get_json_object("game", 2)
        
        # test with wrong content type
        resp = client.put(self.RESOURCE_URL, data=json.dumps(valid))
        assert resp.status_code == 415
        
        resp = client.put(self.INVALID_URL, json=valid)
        assert resp.status_code == 404
        
        # test with another name
        valid["name"] = "Game 3"
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409
        
        # test with valid
        valid["name"] = "Game 2"
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 204

        # test with valid, but without publisher
        valid.pop("publisher")
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 204

        # test with valid, but without genre
        valid.pop("genre")
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 204

        # remove field for 400
        valid["genre"] = "Testing"
        valid.pop("name")
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400

        # test to change the name
        valid["name"] = "Testing"
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 301

    def test_post(self, client):
        valid = _get_json_object("level", 5)
        
        # test with wrong content type
        resp = client.post(self.RESOURCE_URL, data=json.dumps(valid))
        assert resp.status_code == 415

        # try with wrong game
        resp = client.post(self.INVALID_URL, json=valid)
        assert resp.status_code == 404

        # test with valid and see that it exists afterward
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201
        assert resp.headers["Location"].endswith((self.RESOURCE_URL + valid["name"] + "/").replace(" ", "%20"))
        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200
        
        # send same data again for 409
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409
        
        # remove name field for 400
        valid.pop("name")
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400

    def test_delete(self, client):
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 204
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 404
        resp = client.delete(self.INVALID_URL)
        assert resp.status_code == 404


class TestLevelItem(object):
    
    RESOURCE_URL = "/api/games/Game 2/Level 1/"
    RESOURCE_URL_2 = "/api/games/Game 2/Level 2/"
    INVALID_URL = "/api/games/Game 2/Monza/"
    
    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_get_method("profile", client, body, 302)
        _check_control_get_method("up", client, body)
        _check_control_post_method("gss:add-score", client, body, "score", 4)
        _check_control_put_method("edit", client, body, "level")
        assert len(body["items"]) == 3
        for item in body["items"]:
            _check_control_get_method("self", client, item)
            _check_control_get_method("profile", client, item, 302)
        _check_control_delete_method("gss:delete", client, body)
        resp = client.get(self.INVALID_URL)
        assert resp.status_code == 404

    def test_put(self, client):
        valid = _get_json_object("level", 1)
        
        # test with wrong content type
        resp = client.put(self.RESOURCE_URL, data=json.dumps(valid))
        assert resp.status_code == 415
        
        resp = client.put(self.INVALID_URL, json=valid)
        assert resp.status_code == 404
        
        # test with another name
        valid["name"] = "Level 3"
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409
        
        # test with valid
        valid["name"] = "Level 1"
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 204
        
        # remove field for 400
        valid.pop("name")
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400

        # test to change the name
        valid["name"] = "Testing"
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 301


    def test_post(self, client):
        valid = _get_json_object("score", 4)
        
        # test with wrong content type
        resp = client.post(self.RESOURCE_URL, data=json.dumps(valid))
        assert resp.status_code == 415

        # test with wrong level
        resp = client.post(self.INVALID_URL, json=valid)
        assert resp.status_code == 404

        # test with a player that doesn't have a score yet
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201
        assert resp.headers["Location"].endswith((self.RESOURCE_URL + valid["player"] + "/").replace(" ", "%20"))
        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200
        
        # send same data again for 409
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409

        # test to other level, but without a date
        valid.pop("date")
        resp = client.post(self.RESOURCE_URL_2, json=valid)
        assert resp.status_code == 201

        # test with wrong passwod
        valid["password"] = "eaec5029373f916e25da227cc9739c6e"
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 401

        # test if player doesn't exist
        valid["player"] = "player_inv"
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 404

        # remove a field for 400
        valid.pop("value")
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400

    def test_delete(self, client):
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 204
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 404
        resp = client.delete(self.INVALID_URL)
        assert resp.status_code == 404


class TestScoreItem(object):
    
    RESOURCE_URL = "/api/games/Game 2/Level 2/player_2/"
    INVALID_URL = "/api/games/Game 2/Level 2/player_inv/"
    
    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_get_method("profile", client, body, 302)
        _check_control_get_method("up", client, body)
        _check_control_get_method("author", client, body)
        _check_control_get_method("gss:scores-by", client, body)
        _check_control_put_method("edit", client, body, "score")
        _check_control_delete_method("gss:delete", client, body)
        resp = client.get(self.INVALID_URL)
        assert resp.status_code == 404

    def test_put(self, client):
        valid = _get_json_object("score", 2)
        
        # test with wrong content type
        resp = client.put(self.RESOURCE_URL, data=json.dumps(valid))
        assert resp.status_code == 415
        
        # test with invalid URL
        resp = client.put(self.INVALID_URL, json=valid)
        assert resp.status_code == 404
        
        # test with another player
        valid["player"] = "player_3"
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 403

        # test with non-existing player
        valid["player"] = "player_5"
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 404
        
        # test with valid
        valid["player"] = "player_2"
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 204

        # test with valid, but no date
        valid.pop("date")
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 204

        # test with wrong password
        valid["password"] = "a030a4425104607303c346abc26938c3"
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 401

        # remove field for 400
        valid.pop("value")
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400

    def test_delete(self, client):
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 204
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 404
        resp = client.delete(self.INVALID_URL)
        assert resp.status_code == 404

class TestEntry(object):
    RESOURCE_URL = "/api/"

    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_get_method("gss:games-all", client, body)
        _check_control_get_method("gss:players-all", client, body)
