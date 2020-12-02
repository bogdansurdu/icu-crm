import os
from flask import Flask, render_template, request, session
import flaskr.app_config


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )
    app.debug = True
    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import db
    db.init_app(app)

    @app.route('/base')
    def base():
        return render_template('base.html')

    @app.route('/api/test')
    def setupDB():
        db.init_db()
        return 'Created db'

    @app.route('/api/name')
    def changeIdentity():
        if 'user' in request.args:
            session['user'] = request.args.get('user')
        if 'email' in request.args:
            session['email'] = request.args.get('email')
        return 'Changes made'

    from . import tickets
    app.register_blueprint(tickets.bp)

    from . import chat
    app.register_blueprint(chat.chat)

    from . import ad
    app.register_blueprint(ad.bp)

    from . import meetings
    app.register_blueprint(meetings.bp)

    from . import comment
    app.register_blueprint(comment.comm)

    app.jinja_env.globals.update(_build_auth_url=ad.build_auth_url)  # Used in template

    from . import conversations
    app.register_blueprint(conversations.conv)

    return app
