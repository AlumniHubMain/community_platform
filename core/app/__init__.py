import logging
import os
import sys

# TODO: consider fastapi
from flask import Flask


def setup_logger():
    formatter = logging.Formatter('%(asctime)s : %(levelname)s\t[%(name)s]\t%(message)s')
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)

    root_logger = logging.getLogger(__name__)
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(stdout_handler)


def create_app(test_config=None):
    setup_logger()

    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY="dev",
        DATABASE=os.path.join(app.instance_path, "db.sqlite"),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import db
    db.init_app(app)

    from . import user
    app.register_blueprint(user.bp)

    return app
