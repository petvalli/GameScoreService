import click
from flask.cli import with_appcontext
from gamescoreservice import db


class Game(db.Model):
    """
    Game is the root model of the API, levels and scores are under it in the hierarchy.
    Each game will have a unique name and optional additional information.
    "levels" will be filled with all levels of the game and they will be deleted if the game is
     deleted.
    """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False, unique=True)
    publisher = db.Column(db.String(64), nullable=True)
    genre = db.Column(db.String(64), nullable=True)
    
    levels = db.relationship("Level", cascade="all, delete-orphan", back_populates="game")

    def __repr__(self):
        return "G: {} <{}>".format(self.name, self.id)


class Level(db.Model):
    """
    Level "name" must be unique in relation to a game.
    "scores" will be filled with all scores for the level and will be deleted if the level is
    deleted.
    "order" is either "descending" or "ascending" to indicate if lower or higher score is better.
    Levels back-populate Game.
    """

    __table_args__ = (db.UniqueConstraint("name", "game_id", name="_game_level_uc"),)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    order = db.Column(db.String(64), nullable=False, default="descending")
    game_id = db.Column(db.Integer, db.ForeignKey("game.id", ondelete="CASCADE"), nullable=False)

    game = db.relationship("Game", back_populates="levels")
    scores = db.relationship("Score", cascade="all, delete-orphan", back_populates="level")

    def __repr__(self):
        return "L: {} <{}>".format(self.name, self.id)


class Score(db.Model):
    """
    Only one score per player (player_id) per level (level_id) is allowed.
    "value" must be integer and "type" defines if it's a "number" (points, for example) or "time"
    (milliseconds expected).
    "date" is in yyyy-mm-dd hh:mm:ss format.
    Levels and Players are back-populated with scores.
    """

    __table_args__ = (db.UniqueConstraint("level_id", "player_id", name="_level_score_uc"), )

    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(8), nullable=False, default="number")
    date = db.Column(db.String(19), nullable=False)
    level_id = db.Column(db.Integer, db.ForeignKey("level.id", ondelete="CASCADE"), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey("player.id", ondelete="CASCADE"), nullable=False)

    level = db.relationship("Level", back_populates="scores")
    player = db.relationship("Player", back_populates="scores")

    def __repr__(self):
        return "S: {} <{}> L: {}".format(self.value, self.id, self.level_id)


class Player(db.Model):
    """
    The Player model defines a user of the API.
    "name" has to be alphanumeric string that can contain spaces, but no other special chars.
    "unique_name" should be the "name" in lowercase with underscores as space.
    "password" should be an MD5 checksum string of user's real password.
    "scores" contain all scores by a user and they are deleted if the user is deleted.
    """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    unique_name = db.Column(db.String(64), nullable=False, unique=True)
    password = db.Column(db.String(32), nullable=False)

    scores = db.relationship("Score", cascade="all, delete-orphan", back_populates="player")

    def __repr__(self):
        return "{} <{}>".format(self.unique_name, self.id)


@click.command("init-db")
@with_appcontext
def init_db_command():
    """
    Initializes a new database.
    """

    db.create_all()


@click.command("populate-db")
@with_appcontext
def populate_db_command():
    """
    Populates an initialized but empty database with some test values.
    This creates three games (Game 1, Game 2, and Game 3) with three
    levels on each (Level 1, Level 2, Level 3). Score per player is also
    added on each level.
    """

    import hashlib
    from datetime import datetime
    from sqlalchemy.exc import IntegrityError, OperationalError
    try:
        genre = ["Racing", "Puzzle", "Action"]
        for i in range(1, 4):
            g = Game(
                name="Game {}".format(i),
                publisher="Publisher {}".format(i),
                genre=genre[i-1]
            )
            p = Player(
                name="Player {}".format(i),
                unique_name="player_{}".format(i),
                password=hashlib.md5("pw {}".format(i).encode("utf-8")).hexdigest()
            )
            db.session.add(p)
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
                        value=k*100,
                        level_id=lv.id,
                        player_id=k,
                        date=datetime.now().isoformat(' ', 'seconds')
                    )
                    db.session.add(s)
                    db.session.commit()
    except IntegrityError:
        print("Failed to populate the database. Database must be empty.")
    except OperationalError:
        print("Failed to populate the database. Database must be initialized.")
