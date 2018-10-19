import os
import functools

from flask import Flask, session, render_template, request, g
from flask import Blueprint, flash, g, redirect, url_for
from flask_session import Session

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.sql import text
engine = create_engine('postgres://swuklgswqdvenp:3362f809de63cc65ad1f87c891fe7ab68da19a6738f01a3e80e866c0f799a8cf@ec2-50-16-196-57.compute-1.amazonaws.com:5432/dcevpu14st78ms')
from werkzeug.security import check_password_hash, generate_password_hash
app = Flask(__name__)
# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SECRET_KEY"]='dev'

# Check for environment variable
#export DATABASE_URL=postgres://swuklgswqdvenp:3362f809de63cc65ad1f87c891fe7ab68da19a6738f01a3e80e866c0f799a8cf@ec2-50-16-196-57.compute-1.amazonaws.com:5432/dcevpu14st78ms
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

# from flaskr.db import get_db
bp = Blueprint('auth', __name__, url_prefix='/auth')
Session(app)
#  __init__.py from flaskr Tutorial
def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        # a default secret that should be overridden by instance config
        SECRET_KEY='dev',
        # store the database in the instance folder
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )
    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.update(test_config)
    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass


    @app.route('/hello')
    def hello():
        return 'Hello, World!'
    # register the database commands
    from flaskr import db
    db.init_app(app)
    # apply the blueprints to the app
    from flaskr import auth, blog
    app.register_blueprint(auth.bp)
    app.register_blueprint(blog.bp)
    # make url_for('index') == url_for('blog.index')
    # in another app, you might define a separate main index here with
    # app.route, while giving the blog blueprint a url_prefix, but for
    # the tutorial the blog will be the main index
    app.add_url_rule('/', endpoint='index')

    return app
#end from flaskr

# Set up database

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))
error=""

@app.route("/", methods=['GET', 'POST'])
def index():
    g.user = "Line_42"
    subtitle="Home Page"
    return render_template("index.html",subtitle=subtitle, error=error)


@app.route("/registration",methods=['POST','GET'])
def Registration():
    subtitle="Registration Page"
    users = db.execute("SELECT * FROM user_rev1").fetchall()
    #Initiate Variables
    user="TBD"
    password="TBD"
    error = 'Default'
    return render_template("users.html",subtitle=subtitle, error=error, users=users)


@app.route("/register",methods=['POST','GET'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password=generate_password_hash(password)
    users= db.execute("SELECT * FROM user_rev1 WHERE user_rev1.username = :username", {"username": username}).fetchone()
    try:
        username=users.username
        error = 'User {} is already registered.'.format(username)
        subtitle='User {} is already registered.'.format(username)
        session['user_id'] = users['id']
        return render_template("index.html", subtitle=subtitle, users=users,
        username=username,error=RuntimeError)
    except:
        db.execute("INSERT INTO user_rev1 (username, password) VALUES (:username, :password)",
        {"username": username, "password": password})
        db.commit()
        subtitle='Successfully registered {}.'.format(username)
        users= db.execute("SELECT * FROM user_rev1 WHERE user_rev1.username = :username", {"username": username}).fetchone()
        session['user_id'] = users['id']
        return render_template("search.html",subtitle=subtitle,error=session['user_id'])


@app.route("/login",methods=['POST','GET'])
def login():
    subtitle= "Login Page"
    error = "line 58"
    # error = g.user #doesn't carryover from index
    return render_template("users.html",subtitle=subtitle, error=error)


@app.route("/loginuser",methods=['POST','GET'])
def loginuser():
    subtitle="loginuser"
    error="none"
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
    try:
        user = db.execute("SELECT * FROM user_rev1 WHERE user_rev1.username = :username", {"username": username}).fetchone()
        if user is None:
            error = 'Incorrect username.'
            return render_template("index.html", subtitle=subtitle, users=username,
                    username=username,error=error)
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password'
            return render_template("index.html", subtitle=subtitle, user=username,
                    username=username,error=error)
    except:
        return render_template("index.html", subtitle=subtitle, users=username,
                username=username,error="Line 130")
    session.clear()
    session['user_id'] = user['id']
    g.user = db.execute("SELECT * FROM user_rev1 WHERE user_rev1.username = :username", {"username": username}).fetchone()
    return render_template("search.html",subtitle=subtitle,error=session['user_id'])
    #return render_template("users.html",action=register,subtitle=subtitle, error=error)


def login_required(view):
    """View decorator that redirects anonymous users to the login page."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        subtitle="login_required"
        try:
            error=session['user_id']
            if session['user_id'] < 1:
                return render_template("index.html", subtitle=subtitle, error=error)
        except:
            error="User not logged in line 167"
            return render_template("index.html", subtitle=subtitle, error=error)
        return view(**kwargs)
    return wrapped_view


@app.route("/search",methods=['POST','GET'])
@login_required
def search():
    subtitle="search.html from route"
    try:
        return render_template("search.html",subtitle=subtitle,error=session['user_id'])
    except:
        error="User Logged Out"
        return render_template("index.html", subtitle=subtitle, error=error)


#Logout from Flask tutorial
@app.route('/logout', methods=['POST','GET'])
def logout():
    session.clear()
    subtitle="Logged Out"
    error=""
    return render_template("index.html", subtitle=subtitle, error=error)

#decorators from Flask Tutorial
#Not sure this is needed
@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()
        g.user = db.execute("SELECT * FROM user_rev1 WHERE user_rev1.id = :user_id", {"username": user_id}).fetchone()
