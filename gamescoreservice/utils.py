import json
from flask import Response, request, url_for
from gamescoreservice.constants import *
from gamescoreservice.models import *

# create_error_response and MasonBuilder taken from the Programmable Web Project course material:
# https://lovelace.oulu.fi/ohjelmoitava-web/ohjelmoitava-web/


def create_error_response(status_code, title, message=None):
    resource_url = request.path
    body = MasonBuilder(resource_url=resource_url)
    body.add_error(title, message)
    body.add_control("profile", href=ERROR_PROFILE)
    return Response(json.dumps(body), status_code, mimetype=MASON)


class MasonBuilder(dict):
    """
    A convenience class for managing dictionaries that represent Mason
    objects. It provides nice shorthands for inserting some of the more
    elements into the object but mostly is just a parent for the much more
    useful subclass defined next. This class is generic in the sense that it
    does not contain any application specific implementation details.
    """

    def add_error(self, title, details):
        """
        Adds an error element to the object. Should only be used for the root
        object, and only in error scenarios.

        Note: Mason allows more than one string in the @messages property (it's
        in fact an array). However we are being lazy and supporting just one
        message.

        : param str title: Short title for the error
        : param str details: Longer human-readable description
        """

        self["@error"] = {
            "@message": title,
            "@messages": [details],
        }

    def add_namespace(self, ns, uri):
        """
        Adds a namespace element to the object. A namespace defines where our
        link relations are coming from. The URI can be an address where
        developers can find information about our link relations.

        : param str ns: the namespace prefix
        : param str uri: the identifier URI of the namespace
        """

        if "@namespaces" not in self:
            self["@namespaces"] = {}

        self["@namespaces"][ns] = {
            "name": uri
        }

    def add_control(self, ctrl_name, href, **kwargs):
        """
        Adds a control property to an object. Also adds the @controls property
        if it doesn't exist on the object yet. Technically only certain
        properties are allowed for kwargs but again we're being lazy and don't
        perform any checking.

        The allowed properties can be found from here
        https://github.com/JornWildt/Mason/blob/master/Documentation/Mason-draft-2.md

        : param str ctrl_name: name of the control (including namespace if any)
        : param str href: target URI for the control
        """

        if "@controls" not in self:
            self["@controls"] = {}

        self["@controls"][ctrl_name] = kwargs
        self["@controls"][ctrl_name]["href"] = href


class ScoreBuilder(MasonBuilder):
    """
    A subclass to build application specific Mason objects.
    """

    def add_control_players_all(self):
        """
        Adds gss:players-all control, which leads to the Player collection.
        """

        self.add_control(
            "gss:players-all",
            href=url_for("api.playercollection"),
            method="GET",
            title="List all players"
        )

    def add_control_games_all(self):
        """
        Adds gss:games-all control, which leads to the Game collection.
        """

        self.add_control(
            "gss:games-all",
            href=url_for("api.gamecollection"),
            method="GET",
            title="List all games"
        )

    def add_control_scores_by(self, player):
        """
        Adds gss:scores-by control, which leads to the Scores-by collection.
        
        : param str player: Player's unique_name
        """

        self.add_control(
            "gss:scores-by",
            href=url_for("api.scoresbycollection", player=player),
            method="GET",
            title="List all scores by the player"
        )

    def add_control_add_player(self):
        """
        Adds gss:add-player control, which is used to add a player into the Player collection.
        """

        self.add_control(
            "gss:add-player",
            href=url_for("api.playercollection"),
            method="POST",
            encoding="json",
            title="Add a new player",
            schema=Player.get_schema()
        )

    def add_control_add_game(self):
        """
        Adds gss:add-game control, which is used to add a game into the Game collection.
        """

        self.add_control(
            "gss:add-game",
            href=url_for("api.gamecollection"),
            method="POST",
            encoding="json",
            title="Add a new game",
            schema=Game.get_schema()
        )

    def add_control_add_level(self, game):
        """
        Adds gss:add-level control, which is used to add a level into the Game item (collection).

        : param str game: Game's name
        """

        self.add_control(
            "gss:add-level",
            href=url_for("api.gameitem", game=game),
            method="POST",
            encoding="json",
            title="Add a new level",
            schema=Level.get_schema()
        )

    def add_control_add_score(self, game, level):
        """
        Adds gss:add-score control, which is used to add a score into the Level item (collection),
        which is related to a specific Game item.

        : param str game: Game's name
        : param str level: Level's name
        """

        self.add_control(
            "gss:add-score",
            href=url_for("api.levelitem", game=game, level=level),
            method="POST",
            encoding="json",
            title="Add a new score",
            schema=Score.get_schema()
        )

    def add_control_edit_player(self, player):
        """
        Adds edit control, which is used to edit Player item.

        : param str player: Player's unique_name
        """

        self.add_control(
            "edit",
            url_for("api.playeritem", player=player),
            method="PUT",
            encoding="json",
            title="Edit this player",
            schema=Player.get_schema()
        )

    def add_control_edit_game(self, game):
        """
        Adds edit control, which is used to edit Game item.

        : param str game: Game's name
        """

        self.add_control(
            "edit",
            url_for("api.gameitem", game=game),
            method="PUT",
            encoding="json",
            title="Edit this game",
            schema=Game.get_schema()
        )

    def add_control_edit_level(self, game, level):
        """
        Adds edit control, which is used to edit Level item of a specific Game item.

        : param str game: Game's name
        : param str level: Level's name
        """

        self.add_control(
            "edit",
            url_for("api.levelitem", game=game, level=level),
            method="PUT",
            encoding="json",
            title="Edit this level",
            schema=Level.get_schema()
        )

    def add_control_edit_score(self, game, level, player):
        """
        Adds edit control, which is used to edit Score item, which is related to certain game and
        level.

        : param str game: Game's name
        : param str level: Level's name
        : param str player: Player's unique_name
        """

        self.add_control(
            "edit",
            url_for("api.scoreitem", game=game, level=level, player=player),
            method="PUT",
            encoding="json",
            title="Edit this score",
            schema=Score.get_schema()
        )

    def add_control_delete(self, href):
        """
        A generic delete function which should work for all resource types.
        : param str href: Resource's URI
        """

        self.add_control(
            "gss:delete",
            href=href,
            method="DELETE",
            title="Delete this resource"
        )
