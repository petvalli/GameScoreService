import os
from flask import Flask, redirect
from flask_sqlalchemy import SQLAlchemy
from gamescoreservice.constants import *

db = SQLAlchemy()


# Based on http://flask.pocoo.org/docs/1.0/tutorial/factory/#the-application-factory
# Modified to use Flask SQLAlchemy by Programmable Web Project course staff
def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        SQLALCHEMY_DATABASE_URI="sqlite:///" + os.path.join(app.instance_path, "development.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )
    
    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(test_config)
        
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    db.init_app(app)

    from . import models
    from . import api
    app.register_blueprint(api.api_bp)
    app.cli.add_command(models.init_db_command)
    app.cli.add_command(models.populate_db_command)

    @app.route(LINK_RELATIONS_URL)
    def redirect_link_relations():
        """
        Redirect link relations to the Apiary documentation.
        """

        return redirect(APIARY_URL + "link-relations")

    @app.route("/profiles/<profile>/")
    def redirect_profiles(profile):
        """
        Redirect profiles to the Apiary documentation.
        """

        return redirect(APIARY_URL + "profiles")

    return app
